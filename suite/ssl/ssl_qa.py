#!/usr/bin/env python3
import os
import sys

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from config import *
from util import executesql
from util import sysbench_run
from util import utility
from util import rqg_datagen
from util import table_checksum


class SSLCheck(BaseTest):
    def __init__(self):
        super().__init__(ssl=True)

    def sysbench_run(self, test_db):
        sysbench = sysbench_run.SysbenchRun(self.node1, debug)

        sysbench.test_sanity_check(test_db)
        sysbench.test_sysbench_load(test_db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS, SYSBENCH_NORMAL_TABLE_SIZE)
        if encryption == 'YES':
            for i in range(1, int(SYSBENCH_THREADS) + 1):
                self.node1.execute(' alter table ' + test_db + '.sbtest' + str(i) + " encryption='Y'")

    def data_load(self, test_db):
        queries = ['drop database if exists ' + test_db, 'create database ' + test_db]
        self.node1.execute_queries(queries)
        if os.path.isfile(parent_dir + '/util/executesql.py'):
            execute_sql = executesql.GenerateSQL(self.node1, test_db, 1000)
            execute_sql.create_table()
            utility_cmd.check_testcase(0, "SSL QA sample data load")


utility.test_header("PXC SSL test")
ssl_run = SSLCheck()
ssl_run.start_pxc()
ssl_run.sysbench_run('sbtest')
ssl_run.data_load('pxc_dataload_db')
rqg_dataload = rqg_datagen.RQGDataGen(ssl_run.node1, debug)
rqg_dataload.initiate_rqg('examples', 'test', workdir)
if int(version) < int("080000"):
    checksum = table_checksum.TableChecksum(ssl_run.node1, workdir, pt_basedir, debug)
    checksum.sanity_check(ssl_run.pxc_nodes)
    checksum.data_consistency('test,pxc_dataload_db')
else:
    utility_cmd.test_table_count(ssl_run.node1, ssl_run.node2, 'sbtest')
    utility_cmd.test_table_count(ssl_run.node1, ssl_run.node2, 'pxc_dataload_db')