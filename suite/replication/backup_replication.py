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


class SetupReplication(BaseTest):
    def __init__(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        if int(version) < int("080400"):
            my_extra = "--master_info_repository=TABLE --relay_log_info_repository=TABLE"
        else:
            my_extra = None
        super().__init__(extra_config_file=script_dir + '/replication.cnf', my_extra=my_extra)

    def backup_pxc_node(self):
        """ Backup Cluster node using
            Percona XtraBackup tool.
            This method will also do
            sanity check before backup
        """
        pxc_startup.StartCluster.pxb_sanity_check(self.node1, version)
        return pxc_startup.StartCluster.pxb_backup(self.node1, encryption, True, debug)

    def sysbench_run(self, test_db):
        # Sysbench data load
        sysbench = sysbench_run.SysbenchRun(self.node1, debug)

        sysbench.test_sanity_check(test_db)
        sysbench.test_sysbench_load(test_db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS, SYSBENCH_NORMAL_TABLE_SIZE)
        if encryption == 'YES':
            for i in range(1, int(SYSBENCH_TABLE_COUNT) + 1):
                self.node1.execute('alter table ' + test_db + '.sbtest' + str(i) + " encryption='Y'")

    def data_load(self, test_db):
        queries = ["drop database if exists " + test_db, "create database " + test_db]
        self.node1.execute_queries(queries)
        utility_cmd.check_testcase(0,  "PXC : Replication QA sample DB creation")
        # Random data load
        if os.path.isfile(parent_dir + '/util/executesql.py'):
            execute_sql = executesql.GenerateSQL(self.node1, test_db, 1000)
            execute_sql.create_table()
            utility_cmd.check_testcase(0, "PXC : Replication QA sample data load")

        # Add prepared statement SQLs
        self.node1.execute_queries_from_file(parent_dir + '/util/prepared_statements.sql')
        utility_cmd.check_testcase(0, "PXC : Replication QA prepared statements dataload")


utility.test_header("Setup replication using Percona Xtrabackup")
replication_run = SetupReplication()
replication_run.start_pxc()
replication_run.sysbench_run('pxcdb')
replication_run.data_load('pxc_dataload_db')
backup_dir = replication_run.backup_pxc_node()
replication_run.set_number_of_nodes(1)
replication_run.start_ps()
ps_node_1 = replication_run.ps_nodes[0]
utility_cmd.invoke_replication(replication_run.node1, ps_node_1, utility.RplType.BACKUP_REPLICA,
                               backup_dir=backup_dir, version=version)
utility_cmd.replication_io_status(ps_node_1, version)
utility_cmd.replication_sql_status(ps_node_1, version)

replication_run.shutdown_nodes()
replication_run.shutdown_nodes(replication_run.ps_nodes)