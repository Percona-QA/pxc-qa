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
from util import executesql
from util import rqg_datagen

sysbench_run_time = 10


class ConsistencyCheck(BaseTest):
    def __init__(self):
        super().__init__()

    def sysbench_run(self):
        # Sysbench dataload for consistency test
        sysbench = sysbench_run.SysbenchRun(self.node1, debug)

        sysbench.test_sanity_check(db)
        sysbench.test_sysbench_load(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS, SYSBENCH_NORMAL_TABLE_SIZE)
        if encryption == 'YES':
            sysbench.encrypt_sysbench_tables(db)

    def data_load(self, load_db):
        # Random dataload for consistency test
        self.node1.execute("CREATE DATABASE " + load_db)
        execute_sql = executesql.GenerateSQL(self.node1, load_db, 1000)
        execute_sql.create_table()


load_db = 'pxc_dataload_db'

utility.test_header("PXC data consistency test between nodes")
consistency_run = ConsistencyCheck()
consistency_run.start_pxc()
rqg_dataload = rqg_datagen.RQGDataGen(consistency_run.node1, debug)
consistency_run.sysbench_run()
consistency_run.data_load(load_db)
rqg_dataload.pxc_dataload(workdir)
time.sleep(5)
utility_cmd.test_table_count(consistency_run.node1, consistency_run.node2, db)
utility_cmd.test_table_count(consistency_run.node1, consistency_run.node2, db)
utility_cmd.test_table_count(consistency_run.node1, consistency_run.node2, load_db)
