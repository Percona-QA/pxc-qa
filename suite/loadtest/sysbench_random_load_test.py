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
from util import table_checksum


class SysbenchRandomLoadTest(BaseTest):
    def __init__(self):
        super().__init__(my_extra="--max-connections=1500 --innodb_buffer_pool_size=2G --innodb_log_file_size=1G")

    def sysbench_run(self, nodes: list[DbConnection]):
        checksum = ""
        # Sysbench load test
        tables = [50, 1000]  # 100, 300, 600
        threads = [32, 1024]  # 64, 128, 256, 512
        if int(version) < int("080000"):
            checksum = table_checksum.TableChecksum(nodes[0], workdir, pt_basedir, debug)
            checksum.sanity_check(nodes)
        sysbench = sysbench_run.SysbenchRun(nodes[0], debug)
        sysbench.test_sanity_check(db)
        for table_count in tables:
            sysbench.test_sysbench_cleanup(db, table_count, table_count, SYSBENCH_RANDOM_LOAD_TABLE_SIZE)
            sysbench.test_sysbench_load(db, table_count, table_count, SYSBENCH_RANDOM_LOAD_TABLE_SIZE)
            for thread in threads:
                sysbench.sysbench_oltp_read_write(db, table_count, thread,
                                                  SYSBENCH_RANDOM_LOAD_TABLE_SIZE, SYSBENCH_RANDOM_LOAD_RUN_TIME)
                time.sleep(5)
                utility_cmd.test_table_count(nodes[0], nodes[1], db)


utility.test_header("PXC sysbench random load test")

sysbench_random_loadtest = SysbenchRandomLoadTest()
if SERVER == "pxc":
    sysbench_random_loadtest.start_pxc()
    sysbench_random_loadtest.sysbench_run(sysbench_random_loadtest.pxc_nodes)
    sysbench_random_loadtest.shutdown_nodes()
elif SERVER == "ps":
    sysbench_random_loadtest.set_number_of_nodes(1)
    sysbench_random_loadtest.start_ps()
    sysbench_random_loadtest.sysbench_run(sysbench_random_loadtest.ps_nodes)
    sysbench_random_loadtest.shutdown_nodes(sysbench_random_loadtest.ps_nodes)
