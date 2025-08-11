#!/usr/bin/env python3
import os
import sys
import itertools

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from util import sysbench_run
from util import utility


class WSREPProviderRandomTest(BaseTest):
    def __init__(self):
        super().__init__(my_extra="--max-connections=1500 --innodb_buffer_pool_size=2G --innodb_log_file_size=1G")

    def start_random_test(self):
        wsrep_provider_options = {
            "gcache.keep_pages_size": [0, 2],  # 1
            "gcache.recover": ["yes", "no"],
            "gcache.page_size": ["512M", "1024M"],
            "gcache.size": ["512M", "2048M"],  # "1024M"
            #"repl.commit_order": [0, 1, 2, 3]
        }

        keys = wsrep_provider_options.keys()
        values = (wsrep_provider_options[key] for key in keys)
        wsrep_combinations = [dict(zip(keys, combination)) for combination in itertools.product(*values)]
        wsrep_provider_option = ''
        for wsrep_combination in range(0, len(wsrep_combinations)):
            for wsrep_option, wsrep_value in wsrep_combinations[wsrep_combination].items():
                wsrep_provider_option += wsrep_option + "=" + str(wsrep_value) + ";"
            print(datetime.now().strftime("%H:%M:%S ") + " WSREP Provider combination("
                  + wsrep_provider_option + ")")

            self.set_wsrep_provider_options(wsrep_provider_option)
            self.start_pxc()
            sysbench = sysbench_run.SysbenchRun(self.node1, debug)
            sysbench.test_sanity_check(db)
            sysbench.test_sysbench_load(db, use_load_table_size=True)

            sysbench.test_sysbench_oltp_read_write(db, time=300, background=True, use_load_table_size=True)
            sysbench_pid = utility.sysbench_pid()
            print("Sysbench pid : " + sysbench_pid)
            time.sleep(100)
            self.node2.shutdown()
            time.sleep(20)
            utility_cmd.kill_process(sysbench_pid, "sysbench", True)
            utility_cmd.restart_and_check_node(self.node2)
            utility_cmd.wait_for_wsrep_status(self.node2)

            wsrep_provider_option = ''
            time.sleep(5)
            utility_cmd.test_table_count(self.node1, self.node2, db)
            self.shutdown_nodes()


utility.test_header("PXC WSREP provider random test")
sysbench_wsrep_provider_random_test = WSREPProviderRandomTest()
sysbench_wsrep_provider_random_test.start_random_test()
