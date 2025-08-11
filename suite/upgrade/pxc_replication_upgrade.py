#!/usr/bin/env python3
import os
import sys

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from config import *
from util import sysbench_run
from util import utility
from util import rqg_datagen


def get_rpl_conf(rpl_type):
    if rpl_type == utility.RplType.GTID_LESS:
        return parent_dir + '/suite/replication/replication.cnf'
    else:
        return parent_dir + '/suite/replication/gtid_replication.cnf'


class PXCUpgrade(BaseTest):
    def __init__(self):
        super().__init__(vers=Version.LOWER)

    def sysbench_run(self, db, upgrade_type: str):
        # Sysbench dataload for consistency test
        sysbench_ps_node1 = sysbench_run.SysbenchRun(self.ps_nodes[0], debug)

        sysbench_ps_node1.test_sanity_check(db)
        sysbench_ps_node1.test_sysbench_load(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS, SYSBENCH_NORMAL_TABLE_SIZE)
        if int(low_version_num) > int("050700"):
            if encryption == 'YES':
                for i in range(1, int(SYSBENCH_TABLE_COUNT) + 1):
                    self.ps_nodes[0].execute('alter table ' + db + '.sbtest' + str(i) + " encryption='Y'")
        sysbench_node1 = sysbench_run.SysbenchRun(self.node1, debug)
        sysbench_node2 = sysbench_run.SysbenchRun(self.node2, debug)
        sysbench_node3 = sysbench_run.SysbenchRun(self.node3, debug)
        if upgrade_type == 'readwrite':
            sysbench_node1.test_sysbench_oltp_read_write(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                                         SYSBENCH_NORMAL_TABLE_SIZE, 1000, True)
            sysbench_node2.test_sysbench_oltp_read_write(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                                         SYSBENCH_NORMAL_TABLE_SIZE, 1000, True)
            sysbench_node3.test_sysbench_oltp_read_write(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                                         SYSBENCH_NORMAL_TABLE_SIZE, 1000, True)
        elif upgrade_type == 'readonly':
            sysbench_node1.test_sysbench_oltp_read_only(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                                        SYSBENCH_NORMAL_TABLE_SIZE, 1000, True)
            sysbench_node2.test_sysbench_oltp_read_only(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                                        SYSBENCH_NORMAL_TABLE_SIZE, 1000, True)
            sysbench_node3.test_sysbench_oltp_read_only(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                                        SYSBENCH_NORMAL_TABLE_SIZE, 1000, True)

    def rolling_upgrade(self, upgrade_type):
        """ This function will upgrade
            Percona XtraDB Cluster to
            latest version and perform
            table checksum.
        """
        self.sysbench_run('sbtest', upgrade_type)
        time.sleep(10)
        for node in [self.node3, self.node2, self.node1]:
            sysbench_pid = utility.sysbech_node_pid(node.get_node_number())
            utility_cmd.kill_process(sysbench_pid, "sysbench", True)
            pxc_startup.StartCluster.upgrade_pxc_node(node, debug)
        time.sleep(10)
        utility_cmd.replication_io_status(self.node3, high_version_num)
        utility_cmd.replication_sql_status(self.node3, high_version_num)
        sysbench_node = sysbench_run.SysbenchRun(self.node1, debug)
        sysbench_node.test_sysbench_oltp_read_write('sbtest', SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                                    SYSBENCH_NORMAL_TABLE_SIZE, 100)
        time.sleep(15)

        utility_cmd.test_table_count(self.node1, self.node2, 'sbtest')
        utility_cmd.test_table_count(self.node1, self.node2, 'db_galera')
        utility_cmd.test_table_count(self.node1, self.node2, 'db_transactions')
        utility_cmd.test_table_count(self.node1, self.node2, 'db_partitioning')

        self.shutdown_nodes()
        self.shutdown_nodes(self.ps_nodes)


utility.test_header("PXC Asyc non-gtid replication upgrade test : Upgrading from PXC-" + lower_version +
                    " to PXC-" + upper_version)
upgrade_qa = PXCUpgrade()
upgrade_qa.set_extra_conf_file(get_rpl_conf(utility.RplType.GTID_LESS))
upgrade_qa.start_pxc()
saved_number_of_nodes = upgrade_qa.get_number_of_nodes()
upgrade_qa.set_number_of_nodes(1)
upgrade_qa.start_ps()
upgrade_qa.set_number_of_nodes(saved_number_of_nodes)
utility_cmd.invoke_replication(upgrade_qa.ps_nodes[0], upgrade_qa.node3, utility.RplType.GTID_LESS,
                               version=low_version_num)
utility_cmd.replication_io_status(upgrade_qa.node3, low_version_num)
utility_cmd.replication_sql_status(upgrade_qa.node3, low_version_num)
rqg_dataload = rqg_datagen.RQGDataGen(upgrade_qa.node1, debug)
rqg_dataload.pxc_dataload(workdir)
upgrade_qa.rolling_upgrade('none')

utility.test_header("PXC Asyc gtid replication upgrade test : Upgrading from PXC-" + lower_version +
                    " to PXC-" + upper_version)
upgrade_qa.set_extra_conf_file(get_rpl_conf(utility.RplType.GTID))
upgrade_qa.start_pxc()
saved_number_of_nodes = upgrade_qa.get_number_of_nodes()
upgrade_qa.set_number_of_nodes(1)
upgrade_qa.start_ps()
upgrade_qa.set_number_of_nodes(saved_number_of_nodes)
utility_cmd.invoke_replication(upgrade_qa.ps_nodes[0], upgrade_qa.node3, utility.RplType.GTID,
                               version=low_version_num)
utility_cmd.replication_io_status(upgrade_qa.node3, low_version_num)
utility_cmd.replication_sql_status(upgrade_qa.node3, low_version_num)
rqg_dataload = rqg_datagen.RQGDataGen(upgrade_qa.node1, debug)
rqg_dataload.pxc_dataload(workdir)
upgrade_qa.rolling_upgrade('none')
