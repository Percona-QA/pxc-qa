#!/usr/bin/env python3
import os
import shutil
import sys

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from config import *
from util import pxc_startup, executesql
from util import sysbench_run
from util import utility

conf_file = parent_dir + '/conf/mysql_options_pxc80.txt'
random_mysql_error_dir = WORKDIR + '/random_mysql_error'


class RandomMySQLDOptionQA(BaseTest):
    def __init__(self):
        super().__init__(my_extra='--max-connections=1500')

    def data_load(self):
        # Sysbench data load
        sysbench = sysbench_run.SysbenchRun(self.node1, debug)
        sysbench.test_sanity_check(db)
        sysbench.test_sysbench_load(db, 10, 10, SYSBENCH_NORMAL_TABLE_SIZE)

        # Add prepared statement SQLs
        self.node1.execute_queries_from_file(parent_dir + '/util/prepared_statements.sql')

        # Random data load
        if os.path.isfile(parent_dir + '/util/executesql.py'):
            execute_sql = executesql.GenerateSQL(self.node1, db, 1000)
            execute_sql.create_table()


utility.test_header("PXC Random mysqld options test")
mysql_options = open(conf_file)
if os.path.exists(random_mysql_error_dir):
    os.rmdir(random_mysql_error_dir)
os.mkdir(random_mysql_error_dir)

i = 1
for mysql_option in mysql_options:
    i += 1
    random_mysql_option_qa = RandomMySQLDOptionQA()
    # Start PXC cluster for random mysqld options QA
    server_startup = pxc_startup.StartCluster(random_mysql_option_qa.get_number_of_nodes(), debug)
    server_startup.sanity_check()
    option = mysql_option.split('=')[0]
    opt_value = mysql_option.split('=')[1]
    custom_conf_settings = {option: opt_value}
    random_mysql_option_qa.start_pxc(custom_conf_settings=custom_conf_settings, terminate_on_startup_failure=False)

    opt_dir = random_mysql_error_dir + '/' + option + '_' + opt_value
    if len(random_mysql_option_qa.pxc_nodes) != random_mysql_option_qa.get_number_of_nodes():
        if os.path.exists(opt_dir):
            os.rmdir(opt_dir)
        os.mkdir(opt_dir)
        shutil.copytree(WORKDIR + '/log', opt_dir)
        continue
    random_mysql_option_qa.data_load()
    random_mysql_option_qa.shutdown_nodes()
    if i == 7:
        print("Successfully tested cluster with seven mysqld options")
        break
mysql_options.close()
