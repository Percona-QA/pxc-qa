#!/usr/bin/env python3
import os
import sys

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from config import *
from util import sysbench_run
from util import utility
from base_test import *


def run_query(query):
    query_status = os.system(query)
    if int(query_status) != 0:
        print("ERROR! Query execution failed: " + query)
        return 1
    return 0


class ClusterInteraction(BaseTest):
    def __init__(self):
        super().__init__()

    def sysbench_run(self, db, background_run=False):
        # Sysbench dataload for cluster interaction test
        sysbench = sysbench_run.SysbenchRun(self.node1, debug)
        sysbench.test_sanity_check(db)
        sysbench.test_sysbench_load(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS, SYSBENCH_NORMAL_TABLE_SIZE)
        if encryption == 'YES':
            sysbench.encrypt_sysbench_tables(db)
        if background_run:
            sysbench.test_sysbench_oltp_read_write(db, SYSBENCH_TABLE_COUNT, SYSBENCH_TABLE_COUNT,
                                                   SYSBENCH_NORMAL_TABLE_SIZE, SYSBENCH_RUN_TIME, background_run)

    def cluster_interaction_qa(self):
        """ This method will help us to test cluster
            interaction using following test methods.
            1) Flow control
            2) IST
            3) Node joining
        """
        self.sysbench_run(db, True)
        sysbench_pid = utility.sysbench_pid()
        if int(version) > int("050700"):
            utility_cmd.check_testcase(0, "Initiating flow control test")
            #for j in range(1, 2):
            self.node1.execute("set global pxc_strict_mode=DISABLED")
            queries = ["flush table " + db + ".sbtest1 with read lock",
                       "select sleep(120)",
                       "unlock tables"]
            self.node1.execute_queries(queries)
            flow_control_status = 'OFF'
            count = 1
            while flow_control_status != 'OFF':
                if count > 30:
                    print("flow control status isn't OFF, its = " + flow_control_status)
                    break
                flow_control_status = self.node1.execute_get_row("show status like wsrep_flow_control_status")[1]
                time.sleep(1)
                count = count + 1

        utility_cmd.check_testcase(0, "Initiating IST test")

        if debug == 'YES':
            print("shutdown node3")
        self.node3.shutdown()
        time.sleep(30)
        utility_cmd.kill_process(sysbench_pid, "sysbench run")
        utility_cmd.restart_cluster_node(self.node3)
        utility_cmd.startup_check(self.node3)
        utility_cmd.kill_process(sysbench_pid, "sysbench run", True)

        utility_cmd.check_testcase(0, "Initiating Node joining test")
        self.sysbench_run('test_one')
        self.sysbench_run('test_two')
        self.sysbench_run('test_three')
        pxc_startup.StartCluster.join_new_node(self.node3, 4, debug=debug)


cluster_interaction = ClusterInteraction()
utility.test_header('Cluster interaction QA using flow control test')
cluster_interaction.start_pxc()
cluster_interaction.cluster_interaction_qa()
time.sleep(5)
utility_cmd.test_table_count(cluster_interaction.node1, cluster_interaction.node2, db)
