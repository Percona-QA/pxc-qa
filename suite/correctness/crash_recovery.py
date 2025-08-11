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


def restart_node_check_recovery_status(cluster_node: DbConnection):
    """ This method will check the node recovery
        startup status.
    """
    utility_cmd.restart_cluster_node(cluster_node)
    utility_cmd.startup_check(cluster_node)
    utility_cmd.wait_for_wsrep_status(cluster_node)


class CrashRecovery(BaseTest):
    def __init__(self):
        super().__init__()

    def sysbench_run(self):
        # Sysbench dataload for consistency test
        sysbench = sysbench_run.SysbenchRun(self.node1, debug)

        sysbench.test_sanity_check(db)
        sysbench.test_sysbench_load(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS, SYSBENCH_NORMAL_TABLE_SIZE)
        if encryption == 'YES':
            sysbench.encrypt_sysbench_tables(db)
        sysbench.test_sysbench_oltp_read_write(db, SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                                   SYSBENCH_NORMAL_TABLE_SIZE, SYSBENCH_RUN_TIME, True)

    def crash_recovery(self, test_name):
        """ This method will help us to test crash
            recovery using following test methods.
            1) Forceful mysqld termination
            2) Normal restart while active data load in
                primary node
            3) Abnormal restart (multiple restart)
                while active data load in primary node
        """
        self.sysbench_run()
        sysbench_pid = utility.sysbench_pid()
        if test_name == "with_force_kill":
            time.sleep(10)
            utility_cmd.kill_cluster_node(self.node3)
            time.sleep(5)
            utility_cmd.kill_process(sysbench_pid, "sysbench")
            restart_node_check_recovery_status(self.node3)
        elif test_name == "single_restart":
            time.sleep(10)
            result = self.node3.shutdown()
            time.sleep(60)
            if debug == 'YES':
                print("Shutdown node " + str(self.node3.get_node_number()))
            utility_cmd.check_testcase(result, "Shutdown cluster node for crash recovery")
            time.sleep(5)
            utility_cmd.kill_process(sysbench_pid, "sysbench")
            restart_node_check_recovery_status(self.node3)
        elif test_name == "multi_restart":
            for j in range(1, 3):
                result = self.node3.shutdown()
                time.sleep(60)
                if debug == 'YES':
                    print('Shutdown node' + str(self.node3.get_node_number()))
                utility_cmd.check_testcase(result, "Shutdown cluster node for crash recovery")
                time.sleep(10)
                restart_node_check_recovery_status(self.node3)
                sysbench_pid = utility.sysbench_pid()
                if not sysbench_pid:
                    self.sysbench_run()
                    sysbench_pid = utility.sysbench_pid()
                    time.sleep(5)
                utility_cmd.kill_process(sysbench_pid, "sysbench", True)


crash_recovery_run = CrashRecovery()
utility.test_header("Crash recovery QA using forceful mysqld termination")
crash_recovery_run.start_pxc()
checksum = table_checksum.TableChecksum(crash_recovery_run.node1, workdir, pt_basedir, debug)
crash_recovery_run.crash_recovery('with_force_kill')
utility_cmd.test_table_count(crash_recovery_run.node1, crash_recovery_run.node2, db)

utility.test_header('Crash recovery QA using single restart')
crash_recovery_run.start_pxc()
crash_recovery_run.crash_recovery('single_restart')
utility_cmd.test_table_count(crash_recovery_run.node1, crash_recovery_run.node2, db)

utility.test_header('Crash recovery QA using multiple restart')
crash_recovery_run.start_pxc()
crash_recovery_run.crash_recovery('multi_restart')
time.sleep(10)
utility_cmd.test_table_count(crash_recovery_run.node1, crash_recovery_run.node2, db)

