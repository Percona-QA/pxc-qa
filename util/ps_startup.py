#!/usr/bin/env python
# Created by Ramesh Sivaraman, Percona LLC.
# Updated by Parveez Baig
# This will help us to start Percona Server

import json
import os
import subprocess
import shutil

from config import WORKDIR, BASEDIR, PXC_LOWER_BASE, PXC_UPPER_BASE, USER
from util import utility, db_connection
from util.utility import Version, Utility, PS_PORT_SUB_BASE, NODE_PORT_STRIDE, worker_port_band_base, find_available_ports, launch_server

global_workdir = WORKDIR
base_dir = BASEDIR
user = USER
comp_name = 'component_keyring_file'

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../'))


# Create PS configuration file
default_conf = parent_dir + '/conf/ps.cnf'
default_custom_conf = parent_dir + '/conf/custom.cnf'
default_encryption_conf = parent_dir + '/conf/encryption.cnf'


def set_base_dir(server_version : Version):
    global base_dir
    base_dir = BASEDIR
    if server_version == Version.LOWER:
        base_dir = PXC_LOWER_BASE
    elif server_version == Version.HIGHER:
        base_dir = PXC_UPPER_BASE

def ps_allocate_ports(worker_id, node_number):
    base = worker_port_band_base(worker_id) + PS_PORT_SUB_BASE + (node_number - 1) * NODE_PORT_STRIDE
    end = base + NODE_PORT_STRIDE - 1
    try:
        ports = find_available_ports(start=base, end=end, count=1)
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise Exception(f"Failed to allocate PS node port for worker {worker_id}, node {node_number}: {e}") from e
    return ports[0]

def get_workdir(worker_id: int):
    if worker_id > 0:
        return global_workdir + '/w' + str(worker_id)
    else:
        return global_workdir

def component_keyring_file_path(worker_id: int, node_number: int):
    keyring_dir = os.path.join(get_workdir(worker_id), 'keyring')
    os.makedirs(keyring_dir, exist_ok=True)
    return os.path.join(keyring_dir, 'psnode' + str(node_number) + '_' + comp_name)


class StartPerconaServer:
    def __init__(self, number_of_nodes, debug, server_version: Version = None, worker_id: int = 0):
        self.__number_of_nodes = number_of_nodes
        self.__debug = debug
        self.__worker_id = worker_id
        self.__workdir = get_workdir(worker_id)
        if Version is not None:
            set_base_dir(server_version)
        self.__workdir_custom_cnf = self.__workdir + '/conf/custom.cnf'
        self.__workdir_encryption_cnf = self.__workdir + '/conf/encryption.cnf'

    def node_conf(self, node_number: int):
        return self.__workdir + '/conf/ps' + str(node_number) + '.cnf'


    def node_datadir(self, node_number: int):
        return self.__workdir + '/psnode' + str(node_number)


    def node_err_log(self, node_number: int):
        return self.__workdir + '/log/psnode' + str(node_number) + '.err'


    def node_socket(self, node_number: int):
        return self.__workdir + '/psnode' + str(node_number) + '/mysql.sock'


    def init_log(self, node_number: int):
        return self.__workdir + '/log/ps_init' + str(node_number) + '.log'
    
    def test_sanity_check(self):
        """ Sanity check method will remove existing
            data directory and forcefully kill
            running PS mysqld processes. This will also check
            the availability of mysqld binary file.
        """
        # kill existing mysqld process
        os.system("ps -ef | grep '" + self.__workdir + "/conf/ps[0-9].cnf'"
                                                " | grep -v grep | awk '{print $2}' | xargs kill -9 >/dev/null 2>&1")
        result = 0
        # Create log directory
        if not os.path.exists(self.__workdir + '/log'):
            os.mkdir(self.__workdir + '/log')
        # Create configuration directory
        if not os.path.exists(self.__workdir + '/conf'):
            os.mkdir(self.__workdir + '/conf')
        # Check mysqld file
        if not os.path.isfile(base_dir + '/bin/mysqld'):
            print(base_dir + '/bin/mysqld does not exist')
            result = 1
        utility_cmd = utility.Utility(self.__debug)
        utility_cmd.check_testcase(result, "PS: Startup sanity check")

    def create_config(self, conf_extra=None):
        """ Method to create cluster configuration file
            based on the node count. To create configuration
            file it will take default values from conf/pxc.cnf.
            For customised configuration please add your values
            in conf/custom.conf.
        """
        version = Utility.version_check(base_dir)  # Get server version
        port_list = []
        result = 0
        for j in range(1, self.__number_of_nodes + 1):
            port_list.append(ps_allocate_ports(self.__worker_id, j))
        if not os.path.isfile(default_conf):
            print('Default pxc.cnf is missing ' + default_conf)
            result = 1
        else:
            shutil.copy(default_custom_conf, self.__workdir_custom_cnf)
        # Add custom mysqld options in configuration file
        for i in range(1, self.__number_of_nodes + 1):
            conf = self.node_conf(i)
            shutil.copy(default_conf, conf)
            cnf_name = open(conf, 'a+')
            cnf_name.write('\nport=' + str(port_list[i - 1]) + '\n')
            if int(version) > int("050700"):
                cnf_name.write('log_error_verbosity=3\n')
            cnf_name.write('socket=' + self.node_socket(i) + '\n')
            cnf_name.write('server_id=' + str(100 + self.__worker_id + i) + '\n')
            cnf_name.write('!include ' + self.__workdir_custom_cnf + '\n')
            if conf_extra == 'encryption':
                shutil.copy(default_encryption_conf, self.__workdir_encryption_cnf)
                if int(version) < int("080024"):
                    with open(self.__workdir_encryption_cnf, 'a+') as cnf_file:
                        cnf_file.write('early-plugin-load = keyring_file.so\n')
                        cnf_file.write('keyring_file_data = keyring\n')
                cnf_name.write('!include ' + self.__workdir_encryption_cnf + '\n')
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
        cnf_name = open(self.__workdir_custom_cnf, 'a+')
        cnf_name.write('\n')
        cnf_name.write('!include ' + config_file + '\n')
        cnf_name.close()
        utility_cmd = utility.Utility(self.__debug)
        utility_cmd.check_testcase(result, "PS: Adding custom configuration")

    def initialize_server(self, encryption: bool = False):
        """ Method to initialize the server database
            directories. This will initialize the server
            using --initialize-insecure option for
            passwordless authentication.
        """
        result = 1  # return value
        for i in range(1, self.__number_of_nodes + 1):
            conf = self.node_conf(i)
            datadir = self.node_datadir(i)
            err_log = self.node_err_log(i)
            if os.path.exists(datadir):
                os.system('rm -rf ' + datadir + ' >/dev/null 2>&1')
            if not os.path.isfile(conf):
                print('Could not find config file ' + conf)
                exit(1)
            version = Utility.version_check(base_dir)  # Get server version
            initialize_log = self.init_log(i)
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
            if encryption:
                if int(version) >= int("080024"):
                    with open(os.path.join(datadir, 'mysqld.my'), 'w') as manifest_file:
                        json.dump({"components": "file://" + comp_name}, manifest_file, indent=2)
                        manifest_file.write('\n')

                    with open(os.path.join(datadir, comp_name + '.cnf'), 'w') as cnf_file:
                        json.dump({"path": component_keyring_file_path(self.__worker_id, i), "read_only": False}, cnf_file, indent=2)
                        cnf_file.write('\n')

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
            socket = self.node_socket(i)
            conf = self.node_conf(i)
            err_log = self.node_err_log(i)
            mysqld = base_dir + '/bin/mysqld'
            datadir = self.node_datadir(i)
            # Start server
            startup = (mysqld + ' --defaults-file=' + conf + ' --datadir=' + datadir + ' --basedir=' + base_dir +
                       ' ' + my_extra + ' --log-error=' + err_log + ' > ' + err_log + ' 2>&1')
            if self.__debug == 'YES':
                print(startup)
            launch_result = launch_server(startup)
            if launch_result != 0:
                print("Server " + str(i) + " startup failed on launch with exit code " + str(launch_result))
                break
            utility_cmd = utility.Utility(self.__debug)
            node = db_connection.DbConnection(user=user, socket=socket, node_num=i, data_dir=datadir, conf_file=conf,
                                              err_log=err_log, base_dir=base_dir, debug=self.__debug, worker_id=self.__worker_id)
            if verify_startup:
                utility_cmd.startup_check(node)
            ps_nodes.append(node)

        return ps_nodes
