#!/usr/bin/env python3
import os
import sys
import itertools

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from config import *
from util import sysbench_run, executesql
from util import utility
from util import table_checksum
from util import rqg_datagen
from util import pxc_startup


class EncryptionTest(BaseTest):
    def __init__(self):
        super().__init__(encrypt=True)

    def sysbench_run(self):
        # Sysbench data load
        if int(version) < int("080000"):
            checksum = table_checksum.TableChecksum(self.node1, workdir, pt_basedir, debug)
            checksum.sanity_check(self.pxc_nodes)

        sysbench = sysbench_run.SysbenchRun(self.node1, debug)
        sysbench.test_sanity_check(db)
        sysbench.test_sysbench_load(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS, SYSBENCH_LOAD_TEST_TABLE_SIZE)
        sysbench.sysbench_ts_encryption(db, SYSBENCH_THREADS)

    def encryption_qa(self):
        # Encryption QA
        # Create data insert procedure

        option_values = ['ON', 'OFF']

        loop_num = 0
        for val1, val2, val3, val4, val5, val6 in \
                itertools.product(option_values, repeat=6):
            # Start PXC cluster for encryption test
            server_startup = pxc_startup.StartCluster(self.get_number_of_nodes(), debug)
            server_startup.sanity_check()

            options = {"default_table_encryption": val1,
                       "innodb_temp_tablespace_encrypt": val2,
                       "innodb_sys_tablespace_encrypt": val3,
                       "innodb_redo_log_encrypt": val4,
                       "innodb_undo_log_encrypt": val5,
                       "binlog_encryption": val6,
                       "early-plugin-load": "keyring_file.so",
                       "keyring_file_data": "keyring",
                       "encrypt_tmp_files": "ON"}

            server_startup.create_config('encryption', custom_conf_settings=options,
                                         default_encryption_conf=False)

            if options['innodb_sys_tablespace_encrypt'] == 'ON':
                init_extra = ("--innodb_sys_tablespace_encrypt=ON --early-plugin-load=keyring_file.so "
                              "--keyring_file_data=keyring")
                server_startup.initialize_cluster(init_extra)

            else:
                server_startup.initialize_cluster()
            self.pxc_nodes = server_startup.start_cluster()
            self.node1 = self.pxc_nodes[0]
            self.node2 = self.pxc_nodes[1]
            self.node1.test_connection_check()
            self.sysbench_run()
            rqg_dataload = rqg_datagen.RQGDataGen(self.node1, debug)
            rqg_dataload.pxc_dataload(workdir)
            # Add prepared statement SQLs
            self.node1.execute_queries_from_file(parent_dir + '/util/prepared_statements.sql')
            # Random data load
            if os.path.isfile(parent_dir + '/util/executesql.py'):
                execute_sql = executesql.GenerateSQL(self.node1, db, 1000)
                execute_sql.create_table()
                sys.stdout = sys.__stdout__

            # Checksum for tables in test DB for 8.0.
            if int(version) >= int("080000"):
                utility_cmd.test_table_count(self.node1, self.node2, db)

            self.shutdown_nodes()
            loop_num += 1
            if loop_num == 6:
                print("Successfully tested six combinations")
                break


utility.test_header("PXC Encryption test")
encryption_test = EncryptionTest()
encryption_test.encryption_qa()
