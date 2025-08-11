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


class StreamingReplication(BaseTest):
    def __init__(self):
        super().__init__(my_extra="--innodb_buffer_pool_size=2G --innodb_log_file_size=1G")

    def sysbench_run(self):
        # Sysbench data load
        if int(version) < int("080000"):
            checksum = table_checksum.TableChecksum(self.node1, workdir, pt_basedir, debug)
            checksum.sanity_check(self.pxc_nodes)

        sysbench = sysbench_run.SysbenchRun(self.node1, debug)
        sysbench.test_sanity_check(db)
        sysbench.test_sysbench_load(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS, SYSBENCH_LOAD_TEST_TABLE_SIZE)

    def streaming_replication_qa(self):
        # Streaming Replication QA
        # Create data insert procedure
        if debug == 'YES':
            print("Creating streaming replication data insert procedure from " + cwd + '/sr_procedure.sql')
        self.node1.execute("DROP PROCEDURE IF EXISTS test.sr_procedure")
        self.node1.execute_query_from_file(cwd + '/sr_procedure.sql')

        wsrep_trx_fragment_unit = ['bytes', 'rows', 'statements']
        wsrep_trx_fragment_size = [128]  # 1, 2, 4, 8, 16, 64, 128, 256, 512, 1024
        row_count = [100000]  # 100, 1000, 10000
        for trx_fragment_unit, trx_fragment_size, rows in \
                itertools.product(wsrep_trx_fragment_unit, wsrep_trx_fragment_size, row_count):
            if debug == 'YES':
                print("call " + db + ".sr_procedure")
            proc_args = [str(rows), trx_fragment_unit, str(trx_fragment_size)]
            self.node1.call_proc(db + '.sr_procedure', proc_args)

            sr_combination = "DML row count " + proc_args[0] + ", fragment_unit : " + \
                             proc_args[1] + ", fragment_size : " + proc_args[2]
            utility_cmd.check_testcase(0, "SR testcase( " + sr_combination + " )")
            if trx_fragment_unit == 'bytes':
                delete_rows = "delete from " + db + ".sbtest1 limit " + str(rows)
                self.node1.execute(delete_rows)


utility.test_header("PXC Streaming Replication test")
streaming_replication = StreamingReplication()
streaming_replication.start_pxc()
streaming_replication.sysbench_run()
streaming_replication.streaming_replication_qa()
streaming_replication.shutdown_nodes()
