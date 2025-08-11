import os
import itertools
import sys
from config import *
from util.db_connection import DbConnection

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../'))
sys.path.insert(0, parent_dir)
from util import utility

SYSBENCH_DB_CONNECT = " --mysql-user=" + SYSBENCH_USER + \
                      " --mysql-password=" + SYSBENCH_PASS + " --db-driver=mysql "
EXPORT_LUA_PATH = 'export SBTEST_SCRIPTDIR="' + parent_dir + \
                  '/sysbench_lua"; export LUA_PATH="' + parent_dir + \
                  '/sysbench_lua/?;' + parent_dir + '/sysbench_lua/?.lua"'

lua_dir = parent_dir + "/sysbench_lua/"


class SysbenchRun:
    def __init__(self, node: DbConnection, debug):
        self.__node = node
        self.__debug = debug
        self.__utility_cmd = utility.Utility(debug)
        self.__log_dir = WORKDIR + "/log/"

    def sanity_check(self, db):
        # Sanity check for sysbench run
        check_sybench = os.system('which sysbench >/dev/null 2>&1')
        if check_sybench != 0:
            print("ERROR!: sysbench package is not installed")

        queries = ["drop database if exists " + db, "create database " + db]
        self.__node.execute_queries(queries)

        version = self.__utility_cmd.version_check(self.__node.get_base_dir())  # Get version
        create_user_query = ("create user if not exists " + SYSBENCH_USER + "@'localhost' identified by '"
                             + SYSBENCH_PASS + "'")
        grant_query = "grant all on *.* to " + SYSBENCH_USER + "@'localhost'"

        # Create sysbench user
        if int(version) < int("050700"):
            grant_query = grant_query + " identified by '" + SYSBENCH_PASS + "'"
            self.__node.execute(grant_query)
        else:
            self.__node.execute_queries([create_user_query, grant_query])
        return 0

    def test_sanity_check(self, db):
        result = self.sanity_check(db)
        self.__utility_cmd.check_testcase(result, "Sysbench run sanity check")

    def get_params(self, lua_script, table_size, tables, threads, db, log_name):
        return {'lua': lua_dir + lua_script,
                'table-size': str(table_size),
                'tables': str(tables),
                'threads': str(threads),
                'db': db,
                'socket': self.__node.get_socket(),
                'log-file': self.__log_dir + log_name,
                'user': SYSBENCH_USER,
                'password': SYSBENCH_PASS}

    def sysbench_load(self, db, tables, threads, table_size):
        params = self.get_params("oltp_insert.lua", table_size, tables, threads,
                                 db, "sysbench_prepare.log")

        query = ("sysbench {lua} --table-size={table-size} --tables={tables} --threads={threads} --mysql-db={db} "
                 "--mysql-user={user} --mysql-password={password} --db-driver=mysql "
                 "--mysql-socket={socket} prepare > {log-file}").format(**params)

        return self.execute_sysbench_query(query)

    def test_sysbench_load(self, db, tables=SYSBENCH_TABLE_COUNT, threads=SYSBENCH_THREADS,
                           table_size=SYSBENCH_NORMAL_TABLE_SIZE, use_load_table_size: bool = False):
        if use_load_table_size:
            table_size = SYSBENCH_LOAD_TEST_TABLE_SIZE
        result = self.sysbench_load(db, tables, threads, table_size)
        self.__utility_cmd.check_testcase(result, "Sysbench data load with threads " + str(threads))

    def sysbench_ts_encryption(self, db, threads):
        # Check InnoDB system tablespace encryption
        system_ts_encryption_query = ("select encryption from information_schema.innodb_tablespaces where "
                                      "name='innodb_system'")
        if self.__debug == 'YES':
            print(system_ts_encryption_query)
        check_system_ts_encryption = self.__node.execute_get_value(system_ts_encryption_query)
        check_table_encryption_query = "select @@default_table_encryption"
        if self.__debug == 'YES':
            print(check_table_encryption_query)
        # Check default_table_encryption status
        check_table_encryption = self.__node.execute_get_value(check_table_encryption_query)

        for i in range(1, int(threads) - 4):
            query = "CREATE TABLESPACE ts" + str(i) + " ADD DATAFILE 'ts" + str(i) + ".ibd' encryption='Y'"
            self.__node.execute(query)
            if check_table_encryption == 'ON' or check_table_encryption == '1':
                query = "ALTER TABLE " + db + ".sbtest" + str(i) + " tablespace ts" + str(i)
                self.__node.execute(query)

            if check_system_ts_encryption == 'Y':
                if check_table_encryption == 'OFF' or check_table_encryption == '0':
                    query = 'ALTER TABLE ' + db + '.sbtest' + str(i + 5) + " encryption='Y'"
                    self.__node.execute(query)

                query = 'ALTER TABLE ' + db + '.sbtest' + str(i + 5) + ' tablespace=innodb_system'
                self.__node.execute(query)
        return 0

    def sysbench_custom_oltp_load(self, db, table_count, threads, table_size=SYSBENCH_OLTP_TEST_TABLE_SIZE):
        # Create sysbench table structure
        result = self.sysbench_load(db, table_count, table_count, 10000)
        self.__utility_cmd.check_testcase(result, "Sysbench data load")

        params = self.get_params('oltp_read_write.lua', table_size, table_count,
                                 threads, db, "sysbench_oltp_read_write.log")
        params['time'] = str(10)

        rand_types = ['uniform', 'pareto']  # 'gaussian', 'special'
        delete_inserts = [10, 50]  # 20, 30, 40
        index_updates = [10, 50]  # 20, 30, 40
        non_index_updates = [10, 50]  # 20, 30, 40
        for rand_type, delete_insert, index_update, non_index_update in \
                itertools.product(rand_types, delete_inserts, index_updates, non_index_updates):
            params['rand_type'] = rand_type
            params['index_updates'] = str(index_update)
            params['non_index_updates'] = str(non_index_update)
            params['delete_inserts'] = str(delete_insert)

            query = ("sysbench {lua} --table-size={table-size} --tables={tables} --threads={threads} --mysql-db={db} "
                     "--mysql-user={user} --mysql-password={password} --db-driver=mysql "
                     "--mysql-socket={socket} --rand_type={rand_type} --db-ps-mode=disable "
                     "--delete_inserts={delete_inserts} --index_updates={index_updates} "
                     "--time={time} --non_index_updates={non_index_updates} run > {log-file}").format(**params)

            combination = "rand_type:" + rand_type + \
                          ", delete_inserts:" + str(delete_insert) + \
                          ",idx_updates:" + str(index_update) + \
                          ", non_idx_updates:" + str(non_index_update)

            if self.execute_sysbench_query(query) != 0:
                print("ERROR!: sysbench read only(" + combination + ") run is failed")
                exit(1)
            else:
                self.__utility_cmd.check_testcase(0, "Sysbench read only(" + combination + ") run")

    def sysbench_custom_read_qa(self, db, table_count, threads, table_size=SYSBENCH_READ_QA_TABLE_SIZE):
        # Create sysbench table structure
        result = self.sysbench_load(db, table_count, table_count, table_size)
        self.__utility_cmd.check_testcase(result, "Sysbench data load")

        params = self.get_params('oltp_read_only.lua', table_size, table_count, threads,
                                 db, "sysbench_oltp_read_only.log")
        params['time'] = str(10)

        sum_ranges = [2, 6]  # 4
        distinct_ranges = [3, 7]  # 5
        simple_ranges = [5]  # 1, 3
        order_ranges = [8]  # 2, 5
        point_selects = [10, 30]  # 20
        for sum_range, distinct_range, simple_range, order_range, point_select in \
                itertools.product(sum_ranges, distinct_ranges, simple_ranges, order_ranges, point_selects):
            params['distinct_ranges'] = str(distinct_range)
            params['sum_ranges'] = str(sum_range)
            params['simple_ranges'] = str(simple_range)
            params['order_ranges'] = str(order_range)
            params['point_selects'] = str(point_select)

            query = ("sysbench {lua} --table-size={table-size} --tables={tables} --threads={threads} --mysql-db={db} "
                     "--mysql-user={user} --mysql-password={password} --db-driver=mysql "
                     "--mysql-socket={socket} --distinct_ranges={distinct_ranges} --sum_ranges={sum_ranges} "
                     "--simple_ranges={simple_ranges} --order_ranges={order_ranges} --point_selects={point_selects} "
                     "--time={time}  run > {log-file}").format(**params)

            combination = "distinct_rng:" + params['distinct_ranges'] + \
                          ", sum_rng:" + params['sum_ranges'] + \
                          ", simple_rng:" + params['simple_ranges'] + \
                          ", point_selects:" + params['point_selects'] + \
                          ", order_rng:" + params['order_ranges']

            if self.execute_sysbench_query(query) != 0:
                print("ERROR!: sysbench read only(" + combination + ") run is failed")
                exit(1)
            else:
                self.__utility_cmd.check_testcase(0, "Sysbench read only(" + combination + ") run")

    def sysbench_cleanup(self, db, table_count, threads, table_size):

        params = self.get_params('oltp_insert.lua', table_size, table_count, threads,
                                 db, "sysbench_cleanup.log")

        query = ("sysbench {lua} --table-size={table-size} --tables={tables} --threads={threads} --mysql-db={db} "
                 "--mysql-user={user} --mysql-password={password} --db-driver=mysql "
                 "--mysql-socket={socket} cleanup > {log-file}").format(**params)

        return self.execute_sysbench_query(query)

    def test_sysbench_cleanup(self, db, tables, threads, table_size):
        result = self.sysbench_cleanup(db, tables, threads, table_size)
        self.__utility_cmd.check_testcase(result, "Sysbench data cleanup (threads : " + str(threads) + ")")

    def sysbench_oltp_read_write(self, db, table_count, threads, table_size, time, background: bool = False, port=None):
        if background:
            log_file = "sysbench_read_write_" + str(threads) + ".log & "
        else:
            log_file = "sysbench_read_write_" + str(threads) + ".log "

        if port is not None:
            host_to_connect = " --mysql-host=127.0.0.1 --mysql-port=" + str(port)
        else:
            host_to_connect = " --mysql-socket=" + self.__node.get_socket()

        params = self.get_params('oltp_read_write.lua', table_size, table_count, threads,
                                 db, log_file)
        params['time'] = str(time)

        query = ("sysbench {lua} --table-size={table-size} --tables={tables} --threads={threads} --mysql-db={db} "
                 "--mysql-user={user} --mysql-password={password} --db-driver=mysql " + host_to_connect +
                 " --time={time} --db-ps-mode=disable run > {log-file}").format(**params)

        return self.execute_sysbench_query(query)

    def test_sysbench_oltp_read_write(self, db, tables=SYSBENCH_TABLE_COUNT, threads=SYSBENCH_THREADS,
                                      table_size=SYSBENCH_NORMAL_TABLE_SIZE, time=SYSBENCH_RUN_TIME,
                                      background=False, port=None, is_terminate=True, use_load_table_size=False):
        if use_load_table_size:
            table_size = SYSBENCH_LOAD_TEST_TABLE_SIZE
        result = self.sysbench_oltp_read_write(db, tables, threads, table_size, time, background, port)
        self.__utility_cmd.check_testcase(result, "Initiated sysbench oltp run", is_terminate)

    def sysbench_oltp_read_only(self, db, table_count, threads, table_size, time, background: bool = False):
        if background:
            log_file = "sysbench_read_only.log & "
        else:
            log_file = "sysbench_read_only.log "

        params = self.get_params('oltp_read_only.lua', table_size, table_count, threads,
                                 db, log_file)
        params['time'] = str(time)

        # Sysbench OLTP read only run
        query = ("sysbench {lua} --table-size={table-size} --tables={tables} --threads={threads} --mysql-db={db} "
                 "--mysql-user={user} --mysql-password={password} --db-driver=mysql "
                 "--mysql-socket={socket} --time={time} --db-ps-mode=disable run > {log-file}").format(**params)

        return self.execute_sysbench_query(query)

    def test_sysbench_oltp_read_only(self, db, table_count, threads, table_size, time, background=False):
        result = self.sysbench_oltp_read_only(db, table_count, threads, table_size, time, background)
        self.__utility_cmd.check_testcase(result, "Initiated sysbench oltp read only run")

    def sysbench_oltp_write_only(self, db, table_count, threads, table_size, time, background: bool = False):
        if background:
            log_file = "sysbench_write_only.log &"
        else:
            log_file = "sysbench_write_only.log"

        params = self.get_params('oltp_write_only.lua', table_size, table_count, threads,
                                 db, log_file)
        params['time'] = str(time)

        if int(os.system(EXPORT_LUA_PATH)) != 0:
            print("ERROR!: sysbench data load run is failed")
            return 1

        # Sysbench OLTP write only run
        query = ("sysbench {lua} --table-size={table-size} --tables={tables} --threads={threads} --mysql-db={db} "
                 "--mysql-user={user} --mysql-password={password} --db-driver=mysql "
                 "--mysql-socket={socket} --time={time} --db-ps-mode=disable run > {log-file}").format(**params)

        return self.execute_sysbench_query(query)

    def sysbench_custom_table(self, db, table_count, thread, table_size):
        table_format = ['DEFAULT', 'DYNAMIC', 'FIXED', 'COMPRESSED', 'REDUNDANT', 'COMPACT']
        # table_compression = ['ZLIB', 'LZ4', 'NONE']
        if not os.path.exists(lua_dir):
            print("ERROR!: Cannot access 'sysbench_lua': No such directory")
            exit(1)
        for tbl_format in table_format:
            queries = ["drop database if exists " + db + "_" + tbl_format,
                       "create database " + db + "_" + tbl_format]
            self.__node.execute_queries(queries)

            row_format_option = 'sed -i ' \
                                "'s#mysql_table_options = " \
                                '.*."#mysql_table_options = "row_format=' + \
                                tbl_format + '"#g' + "' " + lua_dir + \
                                'oltp_custom_common.lua'
            if self.__debug == 'YES':
                print(row_format_option)
            os.system(row_format_option)
            self.sysbench_load(db + "_" + tbl_format, table_count, thread, table_size)
        row_format_option = 'sed -i ' \
                            "'s#mysql_table_options = " \
                            '.*."#mysql_table_options = "' + \
                            '"#g' + "' " + lua_dir + \
                            'oltp_custom_common.lua'
        if self.__debug == 'YES':
            print(row_format_option)
        os.system(row_format_option)
        return 0

    def test_sysbench_custom_table(self, db, table_count=SYSBENCH_TABLE_COUNT, thread=SYSBENCH_THREADS,
                                   table_size=SYSBENCH_CUSTOMIZED_DATALOAD_TABLE_SIZE):
        result = self.sysbench_custom_table(db, table_count, thread, table_size)
        utility_cmd = utility.Utility(self.__debug)
        utility_cmd.check_testcase(result, "Sysbench data load")

    def sysbench_tpcc_run(self, db, table_count, threads, table_size, time, background: bool = False):
        if background:
            log_file = "sysbench_write_only.log &"
        else:
            log_file = "sysbench_write_only.log"

        params = self.get_params('oltp_write_only.lua', table_size, table_count, threads,
                                 db, log_file)
        params['time'] = str(time)

        if int(os.system(EXPORT_LUA_PATH)) != 0:
            print("ERROR!: sysbench data load run is failed")
            return 1

        # Sysbench OLTP write only run
        query = ("sysbench {lua} --table-size={table-size} --tables={tables} --threads={threads} --mysql-db={db} "
                 "--mysql-user={user} --mysql-password={password} --db-driver=mysql "
                 "--mysql-socket={socket} --time={time} --db-ps-mode=disable run > {log-file}").format(**params)

        return self.execute_sysbench_query(query)

    def execute_sysbench_query(self, query):
        if self.__debug == 'YES':
            print(query)
        if int(os.system(EXPORT_LUA_PATH + ";" + query)) != 0:
            print("ERROR!: sysbench run is failed")
            return 1
        return 0

    def encrypt_sysbench_tables(self, db: str):
        for i in range(1, int(SYSBENCH_TABLE_COUNT) + 1):
            query = "alter table " + db + ".sbtest" + str(i) + " encryption='Y'"
            self.__node.execute(query)
