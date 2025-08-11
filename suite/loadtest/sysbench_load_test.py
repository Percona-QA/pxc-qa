#!/usr/bin/env python3
import os
import sys
import argparse
import time

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from config import *
from util import sysbench_run
from util import utility
from util import table_checksum


class SysbenchLoadTest(BaseTest):
    def __init__(self, number_of_nodes: int = None):
        super().__init__(my_extra="--max-connections=1500 --innodb_buffer_pool_size=2G --innodb_log_file_size=1G")

    def sysbench_run(self, nodes: list[DbConnection]):
        # Sysbench load test
        threads = [32, 1024]  # 64, 128, 256
        if int(version) < int("080000"):
            checksum = table_checksum.TableChecksum(nodes[0], workdir, pt_basedir, debug)
            checksum.sanity_check(nodes)
        for thread in threads:
            sysbench = sysbench_run.SysbenchRun(nodes[0], debug)
            if thread == 32:
                sysbench.test_sanity_check(db)
            sysbench.test_sysbench_cleanup(db, thread, thread, SYSBENCH_LOAD_TEST_TABLE_SIZE)
            sysbench.test_sysbench_load(db, thread, thread, SYSBENCH_LOAD_TEST_TABLE_SIZE)
            time.sleep(60)
            utility_cmd.test_table_count(nodes[0], nodes[2], db)


utility.test_header("PXC sysbench load test")
sysbench_loadtest = SysbenchLoadTest()
if SERVER == "pxc":
    sysbench_loadtest.start_pxc()
    sysbench_loadtest.sysbench_run(sysbench_loadtest.pxc_nodes)
    sysbench_loadtest.shutdown_nodes()
elif SERVER == "ps":
    sysbench_loadtest.set_number_of_nodes(1)
    sysbench_loadtest.start_ps()
    sysbench_loadtest.sysbench_run(sysbench_loadtest.ps_nodes)
    sysbench_loadtest.shutdown_nodes(sysbench_loadtest.ps_nodes)
