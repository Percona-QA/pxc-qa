#!/usr/bin/env python3
import os
import sys

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from util import sysbench_run
from util import utility
from util import table_checksum


class SysbenchOLTPTest(BaseTest):
    def __init__(self):
        super().__init__(my_extra="--max-connections=1500 --innodb_buffer_pool_size=8G --innodb_log_file_size=1G")

    def sysbench_run(self, nodes: list[DbConnection]):
        # Sysbench OLTP Test
        threads = [32, 128]  #64
        if int(version) < int("080000"):
            checksum = table_checksum.TableChecksum(nodes[0], workdir, pt_basedir, debug)
            checksum.sanity_check(nodes)
        sysbench = sysbench_run.SysbenchRun(nodes[0], debug)
        for thread in threads:
            sysbench.test_sanity_check(db)
            sysbench.sysbench_custom_oltp_load(db, 5, thread)
            time.sleep(5)
            if len(nodes) > 1:
                utility_cmd.test_table_count(nodes[0], nodes[1], db)


db = 'test'

utility.test_header("PXC sysbench oltp test")
sysbench_loadtest = SysbenchOLTPTest()
if server == "pxc":
    sysbench_loadtest.start_pxc()
    sysbench_loadtest.sysbench_run(sysbench_loadtest.pxc_nodes)
    sysbench_loadtest.shutdown_nodes()
elif server == "ps":
    sysbench_loadtest.set_number_of_nodes(1)
    sysbench_loadtest.start_ps()
    sysbench_loadtest.sysbench_run(sysbench_loadtest.ps_nodes)
    sysbench_loadtest.shutdown_nodes(sysbench_loadtest.ps_nodes)
