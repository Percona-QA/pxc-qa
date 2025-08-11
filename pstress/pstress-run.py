#!/usr/bin/env python3
import os
import sys
import configparser
import datetime

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from util import utility
from base_test import *
utility_cmd = utility.Utility(debug)
utility_cmd.check_python_version()

# Reading initial configuration
config = configparser.ConfigParser()
config.read('pstress-run.ini')

WORKDIR = config['config']['workdir']
RUNDIR = config['config']['rundir']
BASEDIR = config['config']['basedir']
SERVER = config['config']['server']
NODE = config['config']['node']
USER = config['config']['user']
TRIALS = config['config']['trials']
SAVE_SQL = config['config']['save_sql']
SAVE_TRIALS_WITH_CORE = config['config']['save_trials_with_core']
ENCRYPTION = config['config']['encryption']
MY_EXTRA = config['config']['myextra']
PSTRESS_BIN = config['pstress']['pstress_bin']
PSTRESS_BASE_CONFIG = config['pstress']['pstress_base_config']
TABLES = config['pstress']['tables']
RECORDS = config['pstress']['records']
SEED = config['pstress']['seed']
RECREATE_TABLE = config['pstress']['recreate_table']
OPTIMIZE = config['pstress']['optimize']
RENAME_COLUMN = config['pstress']['rename_column']
ADD_INDEX = config['pstress']['add_index']
DROP_INDEX = config['pstress']['drop_index']
ADD_COLUMN = config['pstress']['add_column']
PRIMARY_KEY_PROBABLITY = config['pstress']['primary_key_probablity']


class PstressRun(BaseTest):
    def __init__(self):
        super().__init__()


utility.test_header("PXC pstress run")
pstress_run = PstressRun()
if server == "pxc":
    pstress_run.start_pxc()
elif server == "ps":
    pstress_run.set_number_of_nodes(1)
    pstress_run.start_ps()
