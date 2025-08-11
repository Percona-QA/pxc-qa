import sys
from datetime import datetime

import mysql.connector
from _mysql_connector import MySQLInterfaceError


class DbConnection:
    def __init__(self, user, password=None, host='localhost', port=None, socket=None, node_num: int = 1, data_dir=None,
                 conf_file=None, err_log=None, base_dir=None, startup_script=None, debug='No'):
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

    def connect(self):
        if self.__socket is None:
            return mysql.connector.connect(host=self.__host, port=self.__port, user=self.__user,
                                           password=self.__password)
        else:
            return mysql.connector.connect(host=self.__host, unix_socket=self.__socket, user=self.__user)

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
            cursor.execute(query)
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
                cursor.execute(query)
        finally:
            if cnx is not None and cnx.is_connected():
                cnx.close()

    def execute_get_value(self, query: str, retries: int = 0):
        cnx = None
        try:
            cnx = self.connect()
            cursor = cnx.cursor(buffered=True)
            cursor.execute(query)
            row = cursor.fetchone()
            if self.__debug == 'YES':
                print(row[0])
            return row[0]
        except MySQLInterfaceError as mysqlInterfaceError:
            if retries > 0:
                print("Retrying, left number of retries" + str(retries))
                self.execute_get_value(query, int(retries - 1))
            else:
                raise Exception(str(mysqlInterfaceError))
        finally:
            # closing database connection.
            if cnx is not None and cnx.is_connected():
                cnx.close()

    def execute_get_values(self, query: str):
        cnx = None
        try:
            cnx = self.connect()
            cursor = cnx.cursor(buffered=True)
            cursor.execute(query)
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
            cursor.execute(query)
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
            cursor.execute(query)
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
            cursor.execute("shutdown")
            print("Shutdown done Node" + str(self.__node_num))
            return 0
        except Exception as e:
            print("Error while connecting to MySQL/Shutting down", e)
            print(e)
            return 0
        finally:
            # closing database connection.
            if cnx is not None and cnx.is_connected():
                cnx.close()

    def execute_query_from_file(self, file_path, multi=True):
        cnx = None
        try:
            cnx = self.connect()
            cursor = cnx.cursor()
            with open(file_path, "r") as file:
                sql_commands = file.read()
                cursor.execute(sql_commands, multi=multi)
            print("Execution of queries completed successfully.")
        except Exception as e:
            print("An error occurred while executing queries from file" + file_path + ": {}".format(e))
            cnx.close()
            sys.exit(1)
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
                    cursor.execute(command)
            except ValueError as msg:
                # Skip and report error
                print("Command skipped: ", msg)
            except Exception as e:
                print("Executing query ", command, "failed due to exception", str(e))
            finally:
                cursor.close()
                cnx.close()
        if self.__debug == 'YES':
            print("Execution of queries from the file ", file_path, "is done")

    def call_proc(self, proc: str, args: list[str]):
        cnx = None
        try:
            cnx = self.connect()
            cursor = cnx.cursor()
            cursor.callproc(proc, args=args)
            print("Execution of stored procedure call completed successfully.")
        except Exception as e:
            print("An error occurred while executing stored procedure" + proc + ": {}".format(e))
            cnx.close()
            sys.exit(1)
        finally:
            if cnx is not None and cnx.is_connected():
                cnx.close()

    def get_port(self):
        return self.execute_get_value("select @@port")

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
