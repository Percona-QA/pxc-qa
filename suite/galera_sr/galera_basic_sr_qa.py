#!/usr/bin/env python3
import os
import sys
import configparser
import argparse
cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from util import pxc_startup
from util import db_connection
from util import sysbench_run
from util import utility
from util import createsql
from util import rqg_datagen
from util import table_checksum
utility_cmd = utility.Utility()
utility_cmd.check_python_version()

# Read argument
parser = argparse.ArgumentParser(prog='PXC replication test', usage='%(prog)s [options]')
parser.add_argument('-e', '--encryption-run', action='store_true',
                    help='This option will enable encryption options')
args = parser.parse_args()
if args.encryption_run is True:
    encryption = 'YES'
else:
    encryption = 'NO'

# Reading initial configuration
config = configparser.ConfigParser()
config.read(parent_dir + '/config.ini')
workdir = config['config']['workdir']
basedir = config['config']['basedir']
user = config['config']['user']
node = config['config']['node']
node1_socket = config['config']['node1_socket']
node2_socket = config['config']['node2_socket']
pt_basedir = config['config']['pt_basedir']
sysbench_threads = 10
sysbench_table_size = 1000
sysbench_run_time = 10


class GaleraSRQA:
    def __init__(self, basedir, workdir, user, socket, node):
        self.workdir = workdir
        self.basedir = basedir
        self.user = user
        self.socket = socket
        self.node = node

    def run_query(self, query):
        query_status = os.system(query)
        if int(query_status) != 0:
            print("ERROR! Query execution failed: " + query)
            return 1
        return 0

    def start_pxc(self):
        # Start PXC cluster for replication test
        dbconnection_check = db_connection.DbConnection(user, self.socket)
        server_startup = pxc_startup.StartCluster(parent_dir, workdir, basedir, int(node))
        result = server_startup.sanity_check()
        utility_cmd.check_testcase(result, "Startup sanity check")
        if encryption == 'YES':
            result = server_startup.create_config('encryption')
            utility_cmd.check_testcase(result, "Configuration file creation")
        result = server_startup.initialize_cluster()
        utility_cmd.check_testcase(result, "Initializing cluster")
        result = server_startup.start_cluster()
        utility_cmd.check_testcase(result, "Cluster startup")
        result = dbconnection_check.connection_check()
        utility_cmd.check_testcase(result, "Database connection")

    def sysbench_run(self, socket, db):
        sysbench = sysbench_run.SysbenchRun(basedir, workdir,
                                            socket)

        result = sysbench.sanity_check(db)
        utility_cmd.check_testcase(result, "SSL QA sysbench run sanity check")
        result = sysbench.sysbench_load(db, sysbench_threads, sysbench_threads, sysbench_table_size)
        utility_cmd.check_testcase(result, "SSL QA sysbench data load")
        if encryption == 'YES':
            for i in range(1, sysbench_threads + 1):
                encrypt_table = basedir + '/bin/mysql --user=root ' \
                    '--socket=/tmp/node1.sock -e "' \
                    ' alter table ' + db + '.sbtest' + str(i) + \
                    " encryption='Y'" \
                    '"; > /dev/null 2>&1'
                os.system(encrypt_table)

    def data_load(self, db, socket):
        if os.path.isfile(parent_dir + '/util/createsql.py'):
            generate_sql = createsql.GenerateSQL('/tmp/dataload.sql', 1000)
            generate_sql.OutFile()
            generate_sql.CreateTable()
            sys.stdout = sys.__stdout__
            create_db = self.basedir + "/bin/mysql --user=root --socket=" + \
                socket + ' -Bse"drop database if exists ' + db + \
                ';create database ' + db + ';" 2>&1'
            result = os.system(create_db)
            utility_cmd.check_testcase(result, "SSL QA sample DB creation")
            data_load_query = self.basedir + "/bin/mysql --user=root --socket=" + \
                socket + ' ' + db + ' -f <  /tmp/dataload.sql >/dev/null 2>&1'
            result = os.system(data_load_query)
            utility_cmd.check_testcase(result, "SSL QA sample data load")


print("\nPXC Galera-4 test")
print("------------------")
galera_run = GaleraSRQA(basedir, workdir, user, node1_socket, node)
galera_run.start_pxc()
galera_run.sysbench_run(node1_socket, 'sbtest')
galera_run.data_load('pxc_dataload_db', node1_socket)
rqg_dataload = rqg_datagen.RQGDataGen(basedir, workdir, user)
rqg_dataload.initiate_rqg('examples', 'test', node1_socket)
version = utility_cmd.version_check(basedir)
if int(version) < int("080000"):
    checksum = table_checksum.TableChecksum(pt_basedir, basedir, workdir, node, node1_socket)
    checksum.sanity_check()
    checksum.data_consistency('test,pxc_dataload_db')
else:
    result = utility_cmd.check_table_count(basedir, 'test', node1_socket, node2_socket)
    utility_cmd.check_testcase(result, "Checksum run for DB: test")
    result = utility_cmd.check_table_count(basedir, 'pxc_dataload_db', node1_socket, node2_socket)
    utility_cmd.check_testcase(result, "Checksum run for DB: pxc_dataload_db")
