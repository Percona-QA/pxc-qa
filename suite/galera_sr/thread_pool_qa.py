#!/usr/bin/env python3
import os
import sys
import itertools

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from config import *
from util import sysbench_run
from util import utility
from util import table_checksum
from util import pxc_startup


class ThreadPooling(BaseTest):
    def __init__(self):
        super().__init__(my_extra="--max-connections=1500 --innodb_buffer_pool_size=2G --innodb_log_file_size=1G")

    def sysbench_run(self, port):
        # Sysbench data load
        checksum = ""
        if int(version) < int("080000"):
            checksum = table_checksum.TableChecksum(self.node1, workdir, pt_basedir, debug)
            checksum.sanity_check(self.pxc_nodes)

        sysbench = sysbench_run.SysbenchRun(self.node1, debug)
        sysbench.test_sanity_check(db)
        sysbench.test_sysbench_load(db, 50, 50, SYSBENCH_NORMAL_TABLE_SIZE)
        # Sysbench OLTP read write run
        sysbench.test_sysbench_oltp_read_write(db, 50, 50, SYSBENCH_NORMAL_TABLE_SIZE,
                                               300, port=port)

    def thread_pooling_qa(self):
        # Thread Pooling QA
        thread_handling_option = ['pool-of-threads', 'one-thread-per-connection']
        thread_pool_size = [2]  # 4, 8
        thread_pool_max_threads = [2, 8]  # 4
        for tp_option, tp_size, tp_max_thread in \
                itertools.product(thread_handling_option, thread_pool_size, thread_pool_max_threads):
            my_extra = "--thread_handling=" + tp_option + " --thread_pool_size=" + str(tp_size) + \
                       " --thread_pool_max_threads=" + str(tp_max_thread)
            # Start PXC cluster for encryption test
            utility_cmd.check_testcase(0, "Thread pooling options : " + my_extra)
            server_startup = pxc_startup.StartCluster(3, debug)
            server_startup.sanity_check()
            server_startup.create_config('none', set_admin_address=True)
            server_startup.initialize_cluster()
            self.pxc_nodes = server_startup.start_cluster(my_extra)
            self.node1 = self.pxc_nodes[0]
            utility_cmd.check_testcase(self.node1.connection_check(), "Database connection")
            self.sysbench_run(33063)
            self.shutdown_nodes(self.pxc_nodes)


utility.test_header("PXC Thread Pooling test")
thread_pooling = ThreadPooling()
thread_pooling.thread_pooling_qa()
