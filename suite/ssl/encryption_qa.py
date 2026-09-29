#!/usr/bin/env python3
import atexit
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

# initialize_cluster(encryption=True, ...) writes the keyring manifest and config into
# the shared basedir. Any other test started from that basedir afterwards would load
# this test's keyring, so qa_framework.py runs this test last and alone, and the files
# are put back the way this test found them when it exits.
GLOBAL_KEYRING_FILES = [os.path.join(BASEDIR, 'bin', 'mysqld.my'),
                        os.path.join(BASEDIR, 'lib', 'plugin', pxc_startup.comp_name + '.cnf')]


def snapshot_global_keyring_files():
    """ Content of each global keyring file, or None if it doesn't exist """
    saved = {}
    for path in GLOBAL_KEYRING_FILES:
        if os.path.isfile(path):
            with open(path, 'rb') as keyring_file:
                saved[path] = keyring_file.read()
        else:
            saved[path] = None
    return saved


def restore_global_keyring_files(saved):
    """ Remove the global keyring files this test created and restore
        any that existed before it started
    """
    for path, content in saved.items():
        try:
            if content is None:
                if os.path.exists(path):
                    os.remove(path)
            else:
                with open(path, 'wb') as keyring_file:
                    keyring_file.write(content)
        except OSError as error:
            print("Could not restore " + path + ": " + str(error))


class EncryptionTest(BaseTest):
    def __init__(self):
        super().__init__(encrypt=True)

    def sysbench_run(self):
        # Sysbench data load
        if int(version) < int("080000"):
            checksum = table_checksum.TableChecksum(self.node1, workdir, pt_basedir, debug)
            checksum.sanity_check(self.pxc_nodes)

        sysbench = sysbench_run.SysbenchRun(self.node1, debug, workdir)
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
            server_startup = pxc_startup.StartCluster(self.get_number_of_nodes(), debug, worker_id=worker_id)
            server_startup.sanity_check()

            options = {"default_table_encryption": val1,
                       "innodb_temp_tablespace_encrypt": val2,
                       "innodb_sys_tablespace_encrypt": val3,
                       "innodb_redo_log_encrypt": val4,
                       "innodb_undo_log_encrypt": val5,
                       "binlog_encryption": val6,
                       "encrypt_tmp_files": "ON"}

            server_startup.create_config(wsrep_extra='encryption', custom_conf_settings=options,
                                         default_encryption_conf=False)

            if options['innodb_sys_tablespace_encrypt'] == 'ON':
                sys_table_encrypt = True
            else:
                sys_table_encrypt = False
            server_startup.initialize_cluster(encryption=True,  sys_table_encrypt=sys_table_encrypt)

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

            # Checksum for tables in test DB for 8.0.
            if int(version) >= int("080000"):
                utility_cmd.test_table_count(self.node1, self.node2, db)

            self.shutdown_nodes()
            loop_num += 1
            if loop_num == 6:
                print("Successfully tested six combinations")
                break


utility.test_header("PXC Encryption test")
# Registered before any cluster starts, so it also runs when a check exits early.
atexit.register(restore_global_keyring_files, snapshot_global_keyring_files())
encryption_test = EncryptionTest()
encryption_test.encryption_qa()
