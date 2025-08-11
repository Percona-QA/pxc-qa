#!/usr/bin/env python3
import os
import sys
import argparse

from util.pxc_startup import StartCluster

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import BaseTest
from config import *
from util import utility, db_connection

# Read argument
parser = argparse.ArgumentParser(prog='PXC Utility', usage='%(prog)s [options]')
parser.add_argument('-e', '--encryption-run', action='store_true',
                    help='This option will enable encryption options')
parser.add_argument('--start', action='store_true',
                    help='Start PXC nodes')
parser.add_argument('--stop', action='store_true',
                    help='Stop PXC nodes')
parser.add_argument('-d', '--debug', action='store_true',
                    help='This option will enable debug logging')
args = parser.parse_args()
if args.encryption_run is True:
    encryption = 'YES'
else:
    encryption = 'NO'
if args.debug is True:
    debug = 'YES'
else:
    debug = 'NO'

utility_cmd = utility.Utility(debug)
utility_cmd.check_python_version()


class PXCUtil(BaseTest):
    def __init__(self):
        super().__init__(my_extra='--max-connections=1500')


pxc_util = PXCUtil()
if args.start is True:
    # Start Cluster
    pxc_util.start_pxc()
    for node in pxc_util.pxc_nodes:
        # Print connection string
        print('\t' + BASEDIR + '/bin/mysql --user=root --socket=' + node.get_socket())
    utility_cmd.check_testcase(0, "PXC connection string")

if args.stop is True:
    StartCluster.kill_mysqld()
