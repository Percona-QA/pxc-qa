#!/usr/bin/env python
# Created by Ramesh Sivaraman, Percona LLC.
# Updated by Parveez Baig
# This will help us to start Percona Server

import os
import subprocess
import random
import shutil

from config import WORKDIR, BASEDIR, PXC_LOWER_BASE, PXC_UPPER_BASE, USER
from util import utility, db_connection
from util.utility import Version, Utility

workdir = WORKDIR
base_dir = BASEDIR
user = USER

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../'))


# Create PS configuration file
default_conf = parent_dir + '/conf/ps.cnf'
default_custom_conf = parent_dir + '/conf/custom.cnf'
default_encryption_conf = parent_dir + '/conf/encryption.cnf'
workdir_custom_conf = workdir + '/conf/custom.cnf'
workdir_encryption_conf = workdir + '/conf/encryption.cnf'


def node_conf(i: int):
    return workdir + '/conf/ps' + str(i) + '.cnf'


def node_datadir(i: int):
    return workdir + '/psnode' + str(i)


def node_err_log(i: int):
    return workdir + '/log/psnode' + str(i) + '.err'


def node_socket(i: int):
    return workdir + '/psnode' + str(i) + '/mysql.sock'


def init_log(i: int):
    return workdir + '/log/ps_init' + str(i) + '.log'


def set_base_dir(server_version : Version):
    global base_dir
    base_dir = BASEDIR
    if server_version == Version.LOWER:
        base_dir = PXC_LOWER_BASE
    elif server_version == Version.HIGHER:
        base_dir = PXC_UPPER_BASE


class StartPerconaServer:
    def __init__(self, number_of_nodes, debug, server_version: Version = None):
        self.__number_of_nodes = number_of_nodes
        self.__debug = debug
        if Version is not None:
            set_base_dir(server_version)

    def test_sanity_check(self):
        """ Sanity check method will remove existing
            data directory and forcefully kill
            running PS mysqld processes. This will also check
            the availability of mysqld binary file.
        """
        # kill existing mysqld process
        os.system("ps -ef | grep '" + workdir + "/conf/ps[0-9].cnf'"
                                                " | grep -v grep | awk '{print $2}' | xargs kill -9 >/dev/null 2>&1")
        result = 0
        # Create log directory
        if not os.path.exists(workdir + '/log'):
            os.mkdir(workdir + '/log')
        # Create configuration directory
        if not os.path.exists(workdir + '/conf'):
            os.mkdir(workdir + '/conf')
        # Check mysqld file
        if not os.path.isfile(base_dir + '/bin/mysqld'):
            print(base_dir + '/bin/mysqld does not exist')
            result = 1
        utility_cmd = utility.Utility(self.__debug)
        utility_cmd.check_testcase(result, "PS: Startup sanity check")

    # This method will help us to check PS version
    def version_check(self):
        # Database version check
        version_info = os.popen(base_dir + "/bin/mysqld --version 2>&1 | "
                                           "grep -oe '[0-9]\.[0-9][\.0-9]*' | head -n1").read()
        version = "{:02d}{:02d}{:02d}".format(int(version_info.split('.')[0]),
                                              int(version_info.split('.')[1]),
                                              int(version_info.split('.')[2]))
        return version

    def create_config(self, conf_extra=None):
        """ Method to create cluster configuration file
            based on the node count. To create configuration
            file it will take default values from conf/pxc.cnf.
            For customised configuration please add your values
            in conf/custom.conf.
        """
        version = Utility.version_check(base_dir)  # Get server version
        port = random.randint(21, 30) * 1004
        port_list = []
        result = 0
        for j in range(1, self.__number_of_nodes + 1):
            port_list += [port + (j * 100)]
        if not os.path.isfile(default_conf):
            print('Default pxc.cnf is missing ' + default_conf)
            result = 1
        else:
            shutil.copy(default_custom_conf, workdir_custom_conf)
        # Add custom mysqld options in configuration file
        for i in range(1, self.__number_of_nodes + 1):
            conf = node_conf(i)
            shutil.copy(default_conf, conf)
            cnf_name = open(conf, 'a+')
            cnf_name.write('\nport=' + str(port_list[i - 1]) + '\n')
            if int(version) > int("050700"):
                cnf_name.write('log_error_verbosity=3\n')
            cnf_name.write('socket=' + node_socket(i) + '\n')
            cnf_name.write('server_id=' + str(100 + i) + '\n')
            cnf_name.write('!include ' + workdir_custom_conf + '\n')
            if conf_extra == 'encryption':
                shutil.copy(default_encryption_conf, workdir_encryption_conf)
                cnf_name.write('!include ' + workdir_encryption_conf + '\n')
            cnf_name.close()

        utility_cmd = utility.Utility(self.__debug)
        utility_cmd.check_testcase(result, "PS: Configuration file creation")

    def add_myextra_configuration(self, config_file):
        """ Adding extra configurations
            based on the testcase
        """
        result = 0
        if not os.path.isfile(config_file):
            print('Custom config ' + config_file + ' is missing')
            result = 1
        # Add custom configurations
        config_file = config_file
        cnf_name = open(workdir_custom_conf, 'a+')
        cnf_name.write('\n')
        cnf_name.write('!include ' + config_file + '\n')
        cnf_name.close()
        utility_cmd = utility.Utility(self.__debug)
        utility_cmd.check_testcase(result, "PS: Adding custom configuration")

    def initialize_server(self):
        """ Method to initialize the server database
            directories. This will initialize the server
            using --initialize-insecure option for
            passwordless authentication.
        """
        result = 1  # return value
        for i in range(1, self.__number_of_nodes + 1):
            conf = node_conf(i)
            datadir = node_datadir(i)
            if os.path.exists(datadir):
                os.system('rm -rf ' + datadir + ' >/dev/null 2>&1')
            if not os.path.isfile(conf):
                print('Could not find config file ' + conf)
                exit(1)
            version = self.version_check()  # Get server version
            initialize_log = init_log(i)
            # Initialize data directory
            if int(version) < int("050700"):
                os.mkdir(datadir)
                initialize_node = (base_dir + '/scripts/mysql_install_db --no-defaults --basedir=' + base_dir +
                                   ' --datadir=' + datadir + ' > ' + initialize_log + ' 2>&1')
            else:
                initialize_node = (base_dir + '/bin/mysqld --no-defaults  --initialize-insecure --basedir=' + base_dir +
                                   ' --datadir=' + datadir + ' > ' + initialize_log + ' 2>&1')
            if self.__debug == 'YES':
                print(initialize_node)
            run_query = subprocess.call(initialize_node, shell=True, stderr=subprocess.DEVNULL)
            result = ("{}".format(run_query))
        utility_cmd = utility.Utility(self.__debug)
        utility_cmd.check_testcase(int(result), "PS: Initializing PS server")

    def start_server(self, my_extra=None, verify_startup: bool = True):
        """ Method to start the cluster nodes. This method
            will also check the startup status.
        """
        if my_extra is None:
            my_extra = ''
        ps_nodes = []
        for i in range(1, self.__number_of_nodes + 1):
            socket = node_socket(i)
            conf = node_conf(i)
            err_log = node_err_log(i)
            mysqld = base_dir + '/bin/mysqld'
            datadir = node_datadir(i)
            # Start server
            startup = (mysqld + ' --defaults-file=' + conf + ' --datadir=' + datadir + ' --basedir=' + base_dir +
                       ' ' + my_extra + ' --log-error=' + err_log + ' > ' + err_log + ' 2>&1 &')
            if self.__debug == 'YES':
                print(startup)
            subprocess.call(startup, shell=True, stderr=subprocess.DEVNULL)
            utility_cmd = utility.Utility(self.__debug)
            node = db_connection.DbConnection(user=user, socket=socket, node_num=i, data_dir=datadir, conf_file=conf,
                                              err_log=err_log, base_dir=base_dir, debug=self.__debug)
            if verify_startup:
                utility_cmd.startup_check(node)
            ps_nodes.append(node)

        return ps_nodes
