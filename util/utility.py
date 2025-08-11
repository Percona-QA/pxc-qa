#!/usr/bin/env python3
import os
import sys
import time
from datetime import datetime
from enum import Enum

import config
from util.db_connection import DbConnection

pstress_bin = config.PSTRESS_BIN

DEFAULT_SERVER_UP_TIMEOUT = 300


class RplType(Enum):
    GTID_LESS = 1
    GTID = 2
    BACKUP_REPLICA = 3


def test_header(test_description: str):
    print('------------------------------------------------------------------------------------')
    print(test_description)
    print('------------------------------------------------------------------------------------')


def test_scenario_header(test_scenario_description: str):
    print('------------------------------------------------------------------------------------')
    print(datetime.now().strftime("%H:%M:%S ") + ' ' + test_scenario_description)
    print('------------------------------------------------------------------------------------')


def sysbench_pid():
    query = 'pidof sysbench'
    return os.popen(query).read().rstrip()


def sysbech_node_pid(node_number: int):
    query = ("ps -ef | grep sysbench | grep -v gep | grep node" + str(node_number) +
             " | awk '{print $2}'")
    return os.popen(query).read().rstrip()


def get_mysql_version(basedir: str):
    query = basedir + "/bin/mysqld --version 2>&1 | grep -oe '[0-9]\.[0-9][\.0-9]*' | head -n1"
    return os.popen(query).read().rstrip()


class Version(Enum):
    LOWER = 1
    HIGHER = 2


class Utility:
    def __init__(self, debug):
        self.debug = debug
        self.outfile = "/tmp/result.file"

    @staticmethod
    def check_testcase(result, testcase, is_terminate: bool = True):
        # print testcase status based on success/failure output.
        now = datetime.now().strftime("%H:%M:%S ")
        if result == 0:
            print(now + ' ' + f'{testcase:100}' + '[ \u2713 ]')
        else:
            print(now + ' ' + f'{testcase:100}' + '[ \u2717 ]')
            if is_terminate:
                exit(1)

    @staticmethod
    def check_python_version():
        """ Check python version. Raise error if the
            version is 3.5 or lower
        """
        if sys.version_info < (3, 6):
            print("\nError! You should use python 3.6 or greater\n")
            exit(1)

    @staticmethod
    def version_check(basedir: str):
        # Get database version number
        version_info = os.popen(basedir + "/bin/mysqld --version 2>&1 "
                                          "| grep -oe '[0-9]\.[0-9][\.0-9]*' | head -n1").read()
        version = "{:02d}{:02d}{:02d}".format(int(version_info.split('.')[0]),
                                              int(version_info.split('.')[1]),
                                              int(version_info.split('.')[2]))
        return version

    def test_table_count(self, node1: DbConnection, node2: DbConnection, db):
        """ This method will compare the table
            count between two nodes
        """
        result = 0
        tables = node1.execute_get_values("show tables in " + db)
        # Compare the table checksum between node1 and node2
        for table in tables:
            table_count_node1 = node1.execute_get_value('checksum table ' + db + '.' + table[0], 4)
            table_count_node2 = node2.execute_get_value('checksum table ' + db + '.' + table[0], 7)
            if table_count_node1 != table_count_node2:
                print("\tTable(" + db + '.' + table[0] + " ) checksum is different")
                result = 1
        self.check_testcase(result, "Checksum run for DB: " + db)

    def replication_io_status(self, node: DbConnection, version: str, channel: str = ''):
        """ This will check replication IO thread
            running status
        """
        if channel == 'none':
            channel = ""

        # Get replica io status
        if int(version) < int("050700"):
            replica_status = node.get_column_value("SHOW SLAVE STATUS", "Slave_IO_Running")
        else:
            replica_status = node.execute_get_value("SELECT SERVICE_STATE FROM "
                                                    "performance_schema.replication_connection_status where "
                                                    "channel_name='" + channel + "'")
        if replica_status not in ['ON', 'Yes']:
            self.check_testcase(1, "Replica IO thread is not running, check replica status")
        else:
            self.check_testcase(0, "Replica IO thread is running fine")

    def replication_sql_status(self, node: DbConnection, version: str, channel: str = ''):
        """ This will check replication SQL thread
            running status
        """
        if channel == 'none':
            channel = ""  # channel name is to identify the replication source

        # Get replica sql status
        if int(version) < int("050700"):
            replica_status = node.get_column_value("SHOW SLAVE STATUS", "Slave_SQL_Running")
        else:
            replica_status = node.execute_get_value("SELECT SERVICE_STATE FROM "
                                                    "performance_schema.replication_applier_status where "
                                                    "channel_name='" + channel + "'")
        if replica_status not in ['YES', 'ON']:
            self.check_testcase(1, "Replica SQL thread is not running, check replica status")
        else:
            self.check_testcase(0, "Replica SQL thread is running fine")

    def invoke_replication(self, source_node: DbConnection, replica_node: DbConnection,
                           repl_mode: RplType, channel_name: str = None,
                           backup_dir='', version: str = None):
        if channel_name is None:
            channel_name = ""  # Set default empty channel name when not set
        # Setup async replication
        source_node.execute("flush logs")
        if repl_mode == RplType.BACKUP_REPLICA:
            data_dir = replica_node.execute_get_value('select @@datadir')
            if self.debug == 'YES':
                print(data_dir)
            query = "cat " + backup_dir + "/xtrabackup_binlog_info | awk '{print $1}'"
            source_log_file = os.popen(query).read().rstrip()
            query = "cat " + backup_dir + "/xtrabackup_binlog_info | awk '{print $2}'"
            source_log_pos = os.popen(query).read().rstrip()
            if self.debug == 'YES':
                print("Binlog data from xtrabackup_binlog_info")
                print("source_log_file: ", source_log_file)
                print("source_log_pos: ", source_log_pos)
        else:
            if version is None or int(version) > int("080300"):
                show_binlog_command = "show binary logs"
            else:
                show_binlog_command = "show master logs"
            source_log_file = source_node.get_column_value(show_binlog_command, "Log_name")
            if self.debug == 'YES':
                print(source_log_file)
            source_log_pos = 4

        source_port = source_node.execute_get_value("select @@port")

        if version is None or int(version) > int("080300"):
            source = "REPLICATION SOURCE"
            host = "SOURCE_HOST"
            port = "SOURCE_PORT"
            user = "SOURCE_USER"
            start_replica_cmd = "START REPLICA"
            source_auto_pos = "SOURCE_AUTO_POSITION"
            source_log_file_var = "SOURCE_LOG_FILE"
            source_log_pos_var = "SOURCE_LOG_POS"

        else:
            source = "MASTER"
            host = "MASTER_HOST"
            port = "MASTER_PORT"
            user = "MASTER_USER"
            start_replica_cmd = "START SLAVE"
            source_auto_pos = "MASTER_AUTO_POSITION"
            source_log_file_var = "MASTER_LOG_FILE"
            source_log_pos_var = "MASTER_LOG_POS"
        change_rpl_source_cmd = ("CHANGE " + source + " TO " + host + "='127.0.0.1', " + port + "="
                                 + str(source_port) + ", " + user + "='root', ")
        if repl_mode == RplType.GTID:
            change_rpl_source_cmd = change_rpl_source_cmd + source_auto_pos + "=1"
        else:
            change_rpl_source_cmd = (change_rpl_source_cmd + source_log_file_var + "='" + source_log_file +
                                     "', " + source_log_pos_var + "=" + str(source_log_pos))
        change_rpl_source_cmd = change_rpl_source_cmd + " for channel '" + channel_name + "'"
        replica_node.execute(change_rpl_source_cmd)
        replica_node.execute(start_replica_cmd)
        self.check_testcase(0, "Initiated replication")

    def pxc_startup_check(self, node: DbConnection):
        # This method will check the pxc node startup status.
        self.startup_check(node)
        self.wait_for_wsrep_status(node)

    def kill_process(self, process_id: str, process_name: str, ignore_error=False):
        kill_cmd = "kill -9 " + process_id
        if ignore_error:
            kill_cmd = kill_cmd + " > /dev/null 2>&1"
        if self.debug == 'YES':
            print("Terminating " + process_name + " run : " + kill_cmd)
        result = os.system(kill_cmd)
        if ignore_error:
            result = 0
        self.check_testcase(result, "Killed " + process_name + " run")
        time.sleep(10)

    def restart_cluster(self, nodes: list[DbConnection]):
        os.system("sed -i 's#safe_to_bootstrap: 0#safe_to_bootstrap: 1#' " +
                  config.WORKDIR + '/node1/grastate.dat')
        for node in nodes:
            self.restart_and_check_node(node)

    def restart_and_check_node(self, node: DbConnection):
        self.restart_cluster_node(node)
        self.startup_check(node)

    def restart_cluster_node(self, node: DbConnection):

        restart_server = "bash " + node.get_startup_script()
        if self.debug == 'YES':
            print(restart_server)
        result = os.system(restart_server)
        self.check_testcase(result, "Starting/Restarting Cluster Node" + str(node.get_node_number()))

    def startup_check(self, node: DbConnection, terminate_on_startup_failure: bool = True):
        """ This method will check the node
            startup status.
        """
        dbconnection_status = -1
        for startup_timer in range(DEFAULT_SERVER_UP_TIMEOUT):
            time.sleep(1)
            dbconnection_status = int(node.connection_check(False))
            if dbconnection_status == 0:
                break
        self.check_testcase(dbconnection_status, "Verify node startup", terminate_on_startup_failure)
        return dbconnection_status

    def wait_for_wsrep_status(self, node: DbConnection, node_sync_timeout=DEFAULT_SERVER_UP_TIMEOUT):
        node_synced = -1
        for startup_timer in range(node_sync_timeout):
            time.sleep(1)
            wsrep_status = (node.execute_get_row("show status like 'wsrep_local_state_comment'")[1]
                            .strip())
            if wsrep_status == "Synced":
                node_synced = 0
                break
        self.check_testcase(node_synced, "Cluster Node recovery is successful")

    def kill_cluster_node(self, node: DbConnection):
        pid_file = node.execute_get_value("select @@pid_file")
        query = 'cat ' + pid_file
        pid = os.popen(query).read().rstrip()
        self.kill_process(pid, "cluster node")

    def kill_cluster_nodes(self):
        if self.debug == 'YES':
            print("Killing existing mysql process using 'kill -9' command")
        os.system("ps -ef | grep '" + config.WORKDIR + "/conf/node[0-9].cnf' | grep -v grep | "
                                                       "awk '{print $2}' | xargs kill -9 >/dev/null 2>&1")

    def pstress_run(self, workdir: str, socket: str, db: str, seed: int, step_num: int = None,
                    tables: int = 25, threads: int = 50, records: int = None, pstress_extra: str = None):
        if not os.path.isfile(pstress_bin):
            print(pstress_bin + ' does not exist')
            exit(1)
        extra_setting = " --records 1000"
        if records is not None:
            extra_setting = " --records " + str(records)
        if step_num is not None:
            extra_setting = extra_setting + " --step " + str(step_num)
        pstress_cmd = pstress_bin + " --database=" + db + " --threads=" + str(threads) + " --logdir=" + \
                      workdir + "/log --log-all-queries --log-failed-queries --user=root --socket=" + \
                      socket + " --seed " + str(seed) + " --tables " + str(tables) + " " + \
                      pstress_extra + " --seconds 300 --grammar-file " + \
                      config.PSTRESS_GRAMMAR_FILE + extra_setting + " > " + \
                      workdir + "/log/pstress_run.log"
        self.check_testcase(0, "PSTRESS RUN command : " + pstress_cmd)
        query_status = os.system(pstress_cmd)
        if int(query_status) != 0:
            self.check_testcase(1, "ERROR!: PSTRESS run failed")
