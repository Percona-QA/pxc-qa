#!/usr/bin/env python3
import os
import sys
import argparse
import time
import subprocess
import itertools
import random
cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from config import *
from util import pxc_startup
from util import db_connection
from util import utility

# Read argument
parser = argparse.ArgumentParser(prog='PXC random mysqld option test', usage='%(prog)s [options]')
parser.add_argument('-e', '--encryption-run', action='store_true',
                    help='This option will enable encryption options')
parser.add_argument('-d', '--debug', action='store_true',
                    help='This option will enable debug logging')
args = parser.parse_args()
if args.encryption_run is True:
    encryption = 'YES'
    PSTRESS_EXTRA = ""
else:
    encryption = 'NO'
    PSTRESS_EXTRA = "--no-encryption"

if args.debug is True:
    debug = 'YES'
else:
    debug = 'NO'

utility_cmd = utility.Utility(debug)
utility_cmd.check_python_version()

class RandomPstressQA:
    def start_pxc(self):
        # Start PXC cluster for pstress run
        dbconnection_check = db_connection.DbConnection(USER, WORKDIR + '/node1/mysql.sock')
        server_startup = pxc_startup.StartCluster(parent_dir, WORKDIR, BASEDIR, int(NODE), debug)
        result = server_startup.sanity_check()
        utility_cmd.check_testcase(result, "Startup sanity check")
        if encryption == 'YES':
            result = server_startup.create_config('encryption')
            utility_cmd.check_testcase(result, "Configuration file creation")
        else:
            result = server_startup.create_config('none')
            utility_cmd.check_testcase(result, "Configuration file creation")
        result = server_startup.initialize_cluster()
        utility_cmd.check_testcase(result, "Initializing cluster")
        result = server_startup.start_cluster('--max-connections=1500')
        utility_cmd.check_testcase(result, "Cluster startup")
        result = dbconnection_check.connection_check()
        utility_cmd.check_testcase(result, "Database connection")
        query = BASEDIR + "/bin/mysql --user=root --socket=" + \
            WORKDIR + "/node1/mysql.sock -e'drop database if exists test " \
                          "; create database test ;' > /dev/null 2>&1"
        if debug == 'YES':
            print(query)
        query_status = os.system(query)
        if int(query_status) != 0:
            # return 1
            print("ERROR!: Could not create test database.")
            exit(1)

    def startup_check(self, cluster_node):
        """ This method will check the node
            startup status.
        """
        ping_query = BASEDIR + '/bin/mysqladmin --user=root --socket=' + \
                     WORKDIR + '/node' + str(cluster_node) + '/mysql.sock ping > /dev/null 2>&1'
        for startup_timer in range(120):
            time.sleep(1)
            ping_check = subprocess.call(ping_query, shell=True, stderr=subprocess.DEVNULL)
            ping_status = ("{}".format(ping_check))
            if int(ping_status) == 0:
                utility_cmd.check_testcase(int(ping_status), "Cluster restart is successful")
                break  # break the loop if mysqld is running

    def data_load(self, socket, db):
        # pstress crash recovery qa
        self.start_pxc()
        n = random.randint(10000, 99999)
        for i in range(1, 10):
            PSTRESS_CMD = PSTRESS_BIN + " --database=" + db + " --threads=50 --logdir=" + \
                         WORKDIR + "/log --log-all-queries --log-failed-queries --user=root --socket=" + \
                         socket + " --seed " + str(n) + " --tables 15 --records 300 " + \
                         PSTRESS_EXTRA + " --seconds 60 --grammar-file " + \
                         PSTRESS_GRAMMAR_FILE + " --step " + str(i) + " > " + \
                         WORKDIR + "/log/pstress_run.log"
            utility_cmd.check_testcase(0, "PSTRESS RUN command : " + PSTRESS_CMD)
            query_status = os.system(PSTRESS_CMD)
            if int(query_status) != 0:
                utility_cmd.check_testcase(1, "ERROR!: PSTRESS run failed")
            # kill existing mysqld process
            if debug == 'YES':
                print("Killing existing mysql process using 'kill -9' command")
            os.system("ps -ef | grep '" + WORKDIR + "/conf/node[0-9].cnf' | grep -v grep | "
                                                    "awk '{print $2}' | xargs kill -9 >/dev/null 2>&1")
            for j in range(1, int(NODE) + 1):
                if j == 1:
                    os.system("sed -i 's#safe_to_bootstrap: 0#safe_to_bootstrap: 1#' " +
                              WORKDIR + '/node1/grastate.dat')
                startup = "bash " + WORKDIR + \
                          '/log/startup' + str(j) + '.sh'
                if debug == 'YES':
                    print(startup)
                os.system(startup)
                self.startup_check(j)


print("-----------------------------")
print("PXC Crash Recovery PSTRESS QA")
print("-----------------------------")
random_pstress_qa = RandomPstressQA()
if not os.path.isfile(PSTRESS_BIN):
    print(PSTRESS_BIN + ' does not exist')
    exit(1)
random_pstress_qa.data_load(WORKDIR + '/node1/mysql.sock', 'test')
