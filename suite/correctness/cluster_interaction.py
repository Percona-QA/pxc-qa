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
        sysbench = sysbench_run.SysbenchRun(self.node1, debug, workdir)
        sysbench.test_sanity_check(db)
        sysbench.test_sysbench_load(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS, SYSBENCH_NORMAL_TABLE_SIZE)
        if encryption:
            sysbench.encrypt_sysbench_tables(db)
        if background_run:
            sysbench.test_sysbench_oltp_read_write(db, SYSBENCH_TABLE_COUNT, SYSBENCH_TABLE_COUNT,
                                                   SYSBENCH_NORMAL_TABLE_SIZE, SYSBENCH_RUN_TIME, background_run)

    @staticmethod
    def flow_control_counter(node: DbConnection, status_name: str):
        return int(node.execute_get_row("show global status like '" + status_name + "'")[1])

    def cluster_interaction_qa(self):
        """ This method will help us to test cluster
            interaction using following test methods.
            1) Flow control
            2) IST
            3) Node joining
        """
        self.sysbench_run(db, True)
        sysbench_pid = utility.sysbench_pid(self.node1)
        if int(version) > int("050700"):
            utility_cmd.check_testcase(0, "Initiating flow control test")
            # Lock a table on node2, which has no local writers: FLUSH TABLE ... WITH READ LOCK
            # pauses its provider, its applier stalls and its recv queue makes it send flow
            # control to node1. Locking node1 instead deadlocks - the FLUSH waits for sysbench's
            # node1 transactions, which can't commit while node1's provider is paused - and a
            # connection lost in that state leaves the provider paused for the rest of the test.
            self.node2.execute("set global pxc_strict_mode=DISABLED")
            fc_sent_before = self.flow_control_counter(self.node2, 'wsrep_flow_control_sent')
            fc_recv_before = self.flow_control_counter(self.node1, 'wsrep_flow_control_recv')
            queries = ["flush table " + db + ".sbtest1 with read lock",
                       "select sleep(120)",
                       "unlock tables"]
            self.node2.execute_queries(queries)

            # node2 requests the pause, node1 (the writer) receives it.
            fc_sent = self.flow_control_counter(self.node2, 'wsrep_flow_control_sent') - fc_sent_before
            fc_recv = self.flow_control_counter(self.node1, 'wsrep_flow_control_recv') - fc_recv_before
            print("Flow control messages sent by node2: " + str(fc_sent) + ", received by node1: " + str(fc_recv))
            utility_cmd.check_testcase(0 if fc_sent > 0 else 1, "Flow control triggered by locked node2")
            utility_cmd.check_testcase(0 if fc_recv > 0 else 1, "Flow control received by writer node1")

            for node in [self.node1, self.node2]:
                flow_control_status = 'ON'
                count = 1
                while flow_control_status != 'OFF':
                    if count > 30:
                        print("flow control status on node" + str(node.get_node_number()) +
                              " isn't OFF, its = " + flow_control_status)
                        break
                    flow_control_status = node.execute_get_row("show status like 'wsrep_flow_control_status'")[1]
                    time.sleep(1)
                    count = count + 1

            self.node2.execute("set global pxc_strict_mode=ENFORCING")

            # Confirm the flow control test didn't leave the cluster unhealthy.
            for node in self.pxc_nodes:
                utility_cmd.wait_for_wsrep_status(node)

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
        pxc_startup.StartCluster.join_new_node(self.node3, 4, debug=debug, encryption=encryption)


cluster_interaction = ClusterInteraction()
utility.test_header('Cluster interaction QA using flow control test')
cluster_interaction.start_pxc()
cluster_interaction.cluster_interaction_qa()
time.sleep(5)
utility_cmd.test_table_count(cluster_interaction.node1, cluster_interaction.node2, db)
