#!/usr/bin/env python3
import os
import sys
import random

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from util import sysbench_run
from util import utility

# Initial configuration
number_of_nodes = 6


class ChaosMonkeyQA(BaseTest):
    def __init__(self):
        super().__init__(number_of_nodes)

    def sysbench_run(self):
        # Sysbench dataload for consistency test
        sysbench = sysbench_run.SysbenchRun(self.node1, debug)

        sysbench.test_sanity_check(db)
        sysbench.test_sysbench_load(db)
        if encryption == 'YES':
            sysbench.encrypt_sysbench_tables(db)
        sysbench.test_sysbench_oltp_read_write(db, background=True)

    def multi_recovery_test(self):
        """ This method will kill 2 random nodes from
            6 node cluster while sysbench is in progress
            and check data consistency after restart.
        """
        nodes = self.pxc_nodes
        nodes.remove(self.node1)
        rand_nodes = random.sample(nodes, 2)
        # random.choices(nodes, k=2)
        if debug == 'YES':
            print("Random nodes selected:")
            for n in rand_nodes:
                print(str(n))
        self.sysbench_run()
        sysbench_pid = utility.sysbench_pid()
        for j in rand_nodes:
            utility_cmd.kill_cluster_node(j)
        utility_cmd.kill_process(sysbench_pid, "sysbench otlp run")
        time.sleep(10)

        for j in rand_nodes:
            utility_cmd.restart_and_check_node(j)
            time.sleep(5)


utility.test_header("PXC ChaosMonkey Style test")
chaosmonkey_qa = ChaosMonkeyQA()
chaosmonkey_qa.start_pxc()
chaosmonkey_qa.multi_recovery_test()
time.sleep(10)
utility_cmd.test_table_count(chaosmonkey_qa.node1, chaosmonkey_qa.node2, db)
