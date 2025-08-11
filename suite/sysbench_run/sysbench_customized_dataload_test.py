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


class SysbenchLoadTest(BaseTest):
    def __init__(self):
        super().__init__(my_extra="--max-connections=1500 --innodb_buffer_pool_size=8G --innodb_log_file_size=1G")

    def sysbench_run(self, node: DbConnection):
        # Sysbench load test
        if int(version) < int("080000"):
            checksum = table_checksum.TableChecksum(node, workdir, pt_basedir, debug)
            checksum.sanity_check(self.pxc_nodes)
        sysbench = sysbench_run.SysbenchRun(node, debug)
        sysbench.test_sanity_check(db)
        sysbench.test_sysbench_custom_table(db)


utility.test_header("PXC sysbench customized data load test")
sysbench_loadtest = SysbenchLoadTest()
if server == "pxc":
    sysbench_loadtest.start_pxc()
    sysbench_loadtest.sysbench_run(sysbench_loadtest.node1)
    sysbench_loadtest.shutdown_nodes()
elif server == "ps":
    sysbench_loadtest.set_number_of_nodes(1)
    sysbench_loadtest.start_ps()
    sysbench_loadtest.sysbench_run(sysbench_loadtest.ps_nodes[0])
    sysbench_loadtest.shutdown_nodes(sysbench_loadtest.ps_nodes)
