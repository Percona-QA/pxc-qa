#!/usr/bin/env python3
import os
import sys


cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from config import *
from util import executesql
from util import sysbench_run
from util import utility
from util import rqg_datagen


class SetupReplication(BaseTest):
    def __init__(self, rpl_type=utility.RplType.GTID_LESS):
        if rpl_type == utility.RplType.GTID:
            extra_conf_file = cwd + '/gtid_replication.cnf'
        else:
            extra_conf_file = cwd + '/replication.cnf'
        super().__init__(extra_config_file=extra_conf_file)
        self.rpl_type = rpl_type

    @staticmethod
    def sysbench_run(node: DbConnection, test_db):
        # Sysbench data load
        sysbench = sysbench_run.SysbenchRun(node, debug)

        sysbench.test_sanity_check(test_db)
        sysbench.test_sysbench_load(test_db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS, SYSBENCH_NORMAL_TABLE_SIZE)
        if encryption == 'YES':
            for i in range(1, int(SYSBENCH_TABLE_COUNT) + 1):
                node.execute('alter table ' + test_db + '.sbtest' + str(i) + " encryption='Y'")

    @staticmethod
    def data_load(node: DbConnection, test_db):
        # Random data load
        queries = ["drop database if exists " + test_db, "create database " + test_db]
        node.execute_queries(queries)
        utility_cmd.check_testcase(0, "Replication QA sample DB creation")

        if os.path.isfile(parent_dir + '/util/executesql.py'):
            execute_sql = executesql.GenerateSQL(node, test_db, 1000)
            execute_sql.create_table()
            utility_cmd.check_testcase(0, "Replication QA sample data load")

        node.execute_queries_from_file(parent_dir + '/util/prepared_statements.sql')
        utility_cmd.check_testcase(0, "Replication QA prepared statements dataload")

    def replication_testcase(self, number_of_ps_nodes: int = 1, is_pxc_source: bool = False, comment: str = None):
        my_extra = ""
        if int(version) < int("080400"):
            my_extra = "--master_info_repository=TABLE --relay_log_info_repository=TABLE"
        if comment == "mta":
            if int(version) > int("080300"):
                my_extra = my_extra + ' --replica-parallel-workers=5'
            else:
                my_extra = my_extra + ' --slave-parallel-workers=5'

        self.start_pxc(my_extra)
        number_of_nodes = self.get_number_of_nodes()
        self.set_number_of_nodes(number_of_ps_nodes)
        self.start_ps(my_extra)
        self.set_number_of_nodes(number_of_nodes)

        source_node = self.ps_nodes[0]
        replica_node = self.node1

        if is_pxc_source:
            temp = source_node
            source_node = replica_node
            replica_node = temp

        if comment == "msr":
            utility_cmd.invoke_replication(source_node, replica_node, self.rpl_type, 'channel1', version=version)
            utility_cmd.invoke_replication(self.ps_nodes[1], replica_node, self.rpl_type, 'channel2',
                                           version=version)
        else:
            utility_cmd.invoke_replication(source_node, replica_node, self.rpl_type, version=version)

        self.sysbench_run(source_node, 'sbtest')
        self.data_load(source_node, 'ps_dataload_db')
        rqg_dataload = rqg_datagen.RQGDataGen(source_node, debug)
        rqg_dataload.pxc_dataload(workdir)

        if comment == "msr":
            utility_cmd.replication_io_status(replica_node, version, 'channel1')
            utility_cmd.replication_sql_status(replica_node, version, 'channel1')
            utility_cmd.replication_io_status(replica_node, version, 'channel2')
            utility_cmd.replication_sql_status(replica_node, version, 'channel2')
        else:
            utility_cmd.replication_io_status(replica_node, version)
            utility_cmd.replication_sql_status(replica_node, version)

        self.shutdown_nodes()
        self.shutdown_nodes(self.ps_nodes)


if __name__ == '__main__':
    replication_run = SetupReplication()
    utility.test_header("NON-GTID PXC->PS async replication")
    replication_run.replication_testcase(is_pxc_source=True)
    utility.test_header("NON-GTID PS->PXC async replication")
    replication_run.replication_testcase()

    if int(version) > int("050700"):
        utility.test_header("NON-GTID PS1->PXC, PS2->PXC Multi source replication")
        replication_run.replication_testcase(2, comment='msr')
        utility.test_header("NON-GTID PS->PXC multi threaded async replication")
        replication_run.replication_testcase(comment='mta')
