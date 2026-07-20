from datetime import datetime

import mysql.connector
from mysql.connector import errors as mysql_errors
from _mysql_connector import MySQLInterfaceError

CONNECTION_TIMEOUT = 60
QUERY_TIMEOUT = 600

# read_timeout/write_timeout and their exceptions require mysql-connector-python 9.2.0+.
ReadTimeoutError = getattr(mysql_errors, 'ReadTimeoutError', None)
WriteTimeoutError = getattr(mysql_errors, 'WriteTimeoutError', None)
QUERY_TIMEOUT_SUPPORTED = ReadTimeoutError is not None and WriteTimeoutError is not None


def _is_query_timeout(exc: BaseException) -> bool:
    return QUERY_TIMEOUT_SUPPORTED and isinstance(exc, (ReadTimeoutError, WriteTimeoutError))


class QueryExecutionError(Exception):
    """Raised when a query fails.
    """

class QueryTimeoutError(Exception):
    """Raised when a query exceeds QUERY_TIMEOUT.
    """

class DbConnection:
    def __init__(self, user, password=None, host='localhost', port=None, socket=None, node_num: int = 1, data_dir=None,
                 conf_file=None, err_log=None, base_dir=None, startup_script=None, debug='No', worker_id: int = 0):
        self.__user = user
        self.__socket = socket
        self.__data_dir = data_dir
        self.__conf_file = conf_file
        self.__err_log = err_log
        self.__debug = debug
        self.__base_dir = base_dir
        self.__startup_script = startup_script
        self.__node_num = node_num
        self.__host = host
        self.__port = port
        self.__password = password
        self.__worker_id = worker_id

    def connect(self, query_timeout: int = QUERY_TIMEOUT):
        connect_kwargs = {
            'host': self.__host,
            'user': self.__user,
            'connection_timeout': CONNECTION_TIMEOUT,
        }
        if QUERY_TIMEOUT_SUPPORTED:
            connect_kwargs['read_timeout'] = query_timeout
            connect_kwargs['write_timeout'] = query_timeout
        if self.__socket is None:
            connect_kwargs['port'] = self.__port
            connect_kwargs['password'] = self.__password
            return mysql.connector.connect(**connect_kwargs)
        connect_kwargs['unix_socket'] = self.__socket
        return mysql.connector.connect(**connect_kwargs)

    def _execute(self, cursor, query, params=None):
        try:
            if params is None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)
        except Exception as query_error:
            if _is_query_timeout(query_error):
                raise QueryTimeoutError(
                    "Query timed out after " + str(query)
                ) from query_error
            raise QueryExecutionError(
                "Error while executing query: " + str(query) + " :: " + str(query_error)
            ) from query_error

    def connection_check(self, log_error_on_failure: bool = True):
        """ Method to test the cluster database connection.
        """
        connection = None
        try:
            # Database connection string
            connection = self.connect()
            if connection.is_connected():
                return 0
        except Exception as mysql_connection_error:
            if log_error_on_failure:
                print("Error while opening connection to server " + str(mysql_connection_error))
            return 1
        finally:
            # closing database connection.
            if connection is not None and connection.is_connected():
                connection.close()

    def test_connection_check(self):
        result = self.connection_check()
        # print testcase status based on success/failure output.
        now = datetime.now().strftime("%H:%M:%S ")
        if result == 0:
            print(now + ' ' + f'{"connection_check":100}' + '[ \u2713 ]')
        else:
            print(now + ' ' + f'{"connection_check":100}' + '[ \u2717 ]')
            exit(1)

    def execute(self, query: str, connection=None, log_query=True):
        cnx = None
        try:
            if connection is not None:
                print("using existing connection")
                cnx = connection
            else:
                cnx = DbConnection.connect(self)
            if self.__debug == 'YES' and log_query:
                print(query)
            cursor = cnx.cursor()
            self._execute(cursor, query)
            return cursor
        finally:
            # closing database connection.
            if connection is None:
                if cnx is not None and cnx.is_connected():
                    cnx.close()
            if connection is not None:
                print("not closing existing connection")

    def execute_queries(self, queries: list[str]):
        cnx = None
        try:
            if self.__debug == 'YES':
                print("Queries to execute :")
                for query in queries:
                    print(query)
            cnx = DbConnection.connect(self)
            cursor = cnx.cursor(buffered=True)
            for query in queries:
                self._execute(cursor, query)
        finally:
            if cnx is not None and cnx.is_connected():
                cnx.close()

    def execute_get_value(self, query: str, retries: int = 0):
        cnx = None
        try:
            cnx = self.connect()
            cursor = cnx.cursor(buffered=True)
            self._execute(cursor, query)
            row = cursor.fetchone()
            if self.__debug == 'YES':
                print(row[0])
            return row[0]
        except QueryExecutionError as query_error:
            if isinstance(query_error.__cause__, MySQLInterfaceError) and retries > 0:
                print("Retrying, left number of retries" + str(retries))
                return self.execute_get_value(query, int(retries - 1))
            raise
        finally:
            # closing database connection.
            if cnx is not None and cnx.is_connected():
                cnx.close()

    def execute_get_values(self, query: str):
        cnx = None
        try:
            cnx = self.connect()
            cursor = cnx.cursor(buffered=True)
            self._execute(cursor, query)
            records = cursor.fetchall()
            print("Number of rows: ", cursor.rowcount)
            if self.__debug == 'YES':
                print("Table rows : " + str(records))
            return records
        finally:
            # closing database connection.
            if cnx is not None and cnx.is_connected():
                cnx.close()

    def execute_get_row(self, query: str):
        cnx = None
        try:
            cnx = self.connect()
            cursor = cnx.cursor()
            self._execute(cursor, query)
            records = cursor.fetchall()
            if self.__debug == 'YES':
                print("Total number of rows in table: ", cursor.rowcount)
            return records[0]
        finally:
            # closing database connection.
            if cnx is not None and cnx.is_connected():
                cnx.close()

    def get_column_value(self, query: str, column: str):
        cnx = None
        try:
            cnx = self.connect()
            cursor = cnx.cursor(buffered=True, dictionary=True)
            self._execute(cursor, query)
            row = cursor.fetchone()
            if self.__debug == 'YES':
                print(row[column])
            return row[column]
        finally:
            if cnx is not None and cnx.is_connected():
                cnx.close()

    def shutdown(self):
        cnx = None
        try:
            cnx = self.connect()
            cursor = cnx.cursor()
            self._execute(cursor, "shutdown")
            print("Shutdown done Node" + str(self.__node_num))
            return 0
        except QueryTimeoutError as query_timeout_error:
            print("Timed out while shutting down node" + str(self.__node_num) + f": {query_timeout_error}")
            raise
        except Exception as e:
            print("Error while connecting to MySQL/Shutting down", e)
            print(e)
            return 0
        finally:
            # closing database connection.
            if cnx is not None and cnx.is_connected():
                cnx.close()

    def execute_query_from_file(self, file_path):
        cnx = None
        try:
            cnx = self.connect()
            cursor = cnx.cursor()
            with open(file_path, "r") as file:
                sql_commands = file.read()
                self._execute(cursor, sql_commands)
            print("Execution of query from file completed successfully.")
        except QueryTimeoutError as query_timeout_error:
            print("Timed out while executing query from file" + file_path + f": {query_timeout_error}")
            raise
        except Exception as e:
            print("An error occurred while executing query from file" + file_path + ": {}".format(e))
            raise
        finally:
            if cnx is not None and cnx.is_connected():
                cnx.close()

    # Execute multiline queries from file. Each query shall be separated from other with $$ symbol
    def execute_queries_from_file(self, file_path):
        # Open and read the file as a single buffer
        with open(file_path, "r") as file:
            sql_file = file.read()
        # SQL commands
        sql_command_set = sql_file.split('$$')

        # Execute every command from the input file
        for command in sql_command_set:
            cnx = self.connect()
            cursor = cnx.cursor(buffered=True)
            try:
                if command.rstrip() != '':
                    self._execute(cursor, command)
            except ValueError as msg:
                # Skip and report error
                print("Command skipped: ", msg)
            except QueryTimeoutError as query_timeout_error:
                print("Timed out while executing query" + command + f": {query_timeout_error}")
                raise
            except Exception as e:
                print("Executing query ", command, "failed due to exception", str(e))
            finally:
                cursor.close()
                cnx.close()
        if self.__debug == 'YES':
            print("Execution of queries from the file ", file_path, "is done")

    def call_proc(self, proc: str, args: list[str], innodb_lock_wait_timeout: int = 0):
        cnx = None
        try:
            cnx = self.connect(query_timeout=QUERY_TIMEOUT * 10)
            cursor = cnx.cursor()
            if innodb_lock_wait_timeout > 0:
                self._execute(cursor, "SET SESSION innodb_lock_wait_timeout = %s",
                              (innodb_lock_wait_timeout,))
            cursor.callproc(proc, args=args)
            print("Execution of stored procedure call completed successfully.")
        except QueryTimeoutError as query_timeout_error:
            print("Timed out while executing stored procedure" + proc + f": {query_timeout_error}")
            raise
        except Exception as e:
            print("An error occurred while executing stored procedure" + proc + ": {}".format(e))
            raise
        finally:
            if cnx is not None and cnx.is_connected():
                cnx.close()

    def get_port(self):
        return self.execute_get_value("select @@port")

    def get_admin_port(self):
        return self.execute_get_value("select @@admin_port")

    def get_mysql_version(self):
        return self.execute_get_value("select @@version")

    def get_user(self):
        return self.__user

    def get_socket(self):
        return self.__socket

    def get_data_dir(self):
        return self.__data_dir

    def get_conf_file(self):
        return self.__conf_file

    def get_startup_script(self):
        return self.__startup_script

    def get_error_log(self):
        return self.__err_log

    def get_base_dir(self):
        return self.__base_dir

    def get_node_number(self):
        return self.__node_num
        
    def get_worker_id(self):
        return self.__worker_id

