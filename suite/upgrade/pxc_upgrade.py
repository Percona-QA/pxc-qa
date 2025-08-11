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


class PXCUpgrade(BaseTest):
    def __init__(self):
        super().__init__(vers=Version.LOWER)

    def join_higher_version_node(self):
        # Start PXC cluster for upgrade test
        self.pxc_nodes.append(pxc_startup.StartCluster.join_new_upgraded_node(self.node3, 4, debug))

    def sysbench_run(self, upgrade_type):
        # Sysbench dataload for consistency test
        sysbench_node1 = sysbench_run.SysbenchRun(self.node1, debug)

        sysbench_node1.test_sanity_check(db)
        sysbench_node1.test_sysbench_load(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS, SYSBENCH_NORMAL_TABLE_SIZE)
        if int(low_version_num) > int("050700"):
            if encryption == 'YES':
                for i in range(1, int(SYSBENCH_TABLE_COUNT) + 1):
                    self.node1.execute('alter table ' + db + '.sbtest' + str(i) + " encryption='Y'")

        sysbench_node2 = sysbench_run.SysbenchRun(self.node2, debug)
        sysbench_node3 = sysbench_run.SysbenchRun(self.node3, debug)
        if upgrade_type == 'readwrite' or upgrade_type == 'readwrite_sst':
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
        self.sysbench_run(upgrade_type)
        time.sleep(5)
        for node in [self.node3, self.node2, self.node1]:
            sysbench_pid = utility.sysbech_node_pid(node.get_node_number())
            utility_cmd.kill_process(sysbench_pid, "sysbench run", True)
            if node == self.node3 and upgrade_type == 'readwrite_sst':
                node_to_add_load = self.node1
            else:
                node_to_add_load = None
            cnf_replace = {"wsrep_slave_threads": "30"}
            if 'readwrite' in upgrade_type:
                pxc_startup.StartCluster.upgrade_pxc_node(node, debug, node_to_add_load, cnf_replace, 600)
            else:
                pxc_startup.StartCluster.upgrade_pxc_node(node, debug, node_to_add_load, cnf_replace)
        time.sleep(60)
        sysbench_node = sysbench_run.SysbenchRun(self.node1, debug)
        sysbench_node.test_sysbench_oltp_read_write(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                                    SYSBENCH_NORMAL_TABLE_SIZE, 100)
        time.sleep(5)

        utility_cmd.test_table_count(self.node1, self.node2, 'test')
        utility_cmd.test_table_count(self.node1, self.node2, 'db_galera')
        utility_cmd.test_table_count(self.node1, self.node2, 'db_transactions')
        utility_cmd.test_table_count(self.node1, self.node2, 'db_partitioning')
        self.shutdown_nodes()


utility.test_header("PXC Upgrade test : Upgrading from PXC-" + lower_version + " to PXC-" + upper_version)

utility.test_scenario_header(" Rolling upgrade without active workload")
upgrade_qa = PXCUpgrade()
upgrade_qa.start_pxc()
rqg_dataload = rqg_datagen.RQGDataGen(upgrade_qa.node1, debug)
rqg_dataload.pxc_dataload(workdir)
upgrade_qa.rolling_upgrade('none')

utility.test_scenario_header("Rolling upgrade with active readonly workload")
upgrade_qa.start_pxc()
rqg_dataload = rqg_datagen.RQGDataGen(upgrade_qa.node1, debug)
rqg_dataload.pxc_dataload(workdir)
upgrade_qa.rolling_upgrade('readonly')

utility.test_scenario_header(" Rolling upgrade with active read/write workload enforcing SST on node-join)")
upgrade_qa.start_pxc()
rqg_dataload = rqg_datagen.RQGDataGen(upgrade_qa.node1, debug)
rqg_dataload.pxc_dataload(workdir)
upgrade_qa.rolling_upgrade('readwrite_sst')

utility.test_scenario_header(" Rolling upgrade with active read/write workload enforcing IST on node-join)")
upgrade_qa.set_wsrep_provider_options('gcache.keep_pages_size=5;gcache.page_size=1024M;gcache.size=1024M;')
upgrade_qa.start_pxc()
rqg_dataload = rqg_datagen.RQGDataGen(upgrade_qa.node1, debug)
rqg_dataload.pxc_dataload(workdir)
upgrade_qa.rolling_upgrade('readwrite')
if int(version) > int("080000"):
    utility.test_scenario_header("Mix of PXC-" + lower_version + " and PXC-" + upper_version +
                                 " (without active workload)")
    upgrade_qa = PXCUpgrade()
    upgrade_qa.start_pxc()
    upgrade_qa.join_higher_version_node()
    utility.test_scenario_header("Mix of PXC-" + lower_version + " and PXC-" + upper_version +
                                 " (with active read/write workload)")
    upgrade_qa.set_wsrep_provider_options('gcache.keep_pages_size=5;gcache.page_size=1024M;gcache.size=1024M;')
    upgrade_qa.start_pxc()
    rqg_dataload = rqg_datagen.RQGDataGen(upgrade_qa.node1, debug)
    rqg_dataload.pxc_dataload(workdir)
    upgrade_qa.sysbench_run('readwrite')
    upgrade_qa.join_higher_version_node()
    upgrade_qa.shutdown_nodes()
