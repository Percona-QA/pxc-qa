#!/usr/bin/env python
# Created by Ramesh Sivaraman, Percona LLC.
# Updated by Parveez Baig
# This will help us to start Percona XtraDB Cluster, Upgrade cluster nodes, Backup the cluster nodes.

from gzip import BadGzipFile
import json
import os
import subprocess
import shutil
import time

from distutils.spawn import find_executable

from util import sanity, utility, sysbench_run
from util import db_connection
from config import *
from util.db_connection import DbConnection
from util.utility import (Version, Utility, NODE_PORT_STRIDE, worker_port_band_base, find_available_ports,
                          launch_server)

global_workdir = WORKDIR
base_dir = BASEDIR
user = USER
comp_name = 'component_keyring_file'
cluster_keyring_file_name = 'cluster_' + comp_name
node_keyring_file_name = 'node_' + '{node_number}' + '_' + comp_name
ps_node_keyring_file_name = 'psnode' + '{node_number}' + '_' + comp_name

higher_version_basedir = PXC_UPPER_BASE
lower_base_dir = PXC_LOWER_BASE
DEFAULT_SERVER_UP_TIMEOUT = 300

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../'))

default_pxc_cnf = os.path.join(parent_dir, 'conf', 'pxc.cnf')
default_custom_cnf = os.path.join(parent_dir, 'conf', 'custom.cnf')
encryption_cnf = os.path.join(parent_dir, 'conf', 'encryption.cnf')

BACKUP_TIMEOUT = 1800


def pxc_allocate_ports(worker_id, node_number, set_admin_address: bool = False):
    slot_base = (worker_port_band_base(worker_id) + (node_number - 1) * NODE_PORT_STRIDE)
    slot_end = slot_base + NODE_PORT_STRIDE - 1

    if set_admin_address:
        count = 5
    else:
        count = 4

    try:
        ports = find_available_ports(start=slot_base, end=slot_end, count=count)
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise Exception(f"Failed to allocate PXC ports for worker {worker_id}, node {node_number}: {e}") from e
    if set_admin_address:
        return ports[0], ports[1], ports[2], ports[3], ports[4]
    return ports[0], ports[1], ports[2], ports[3]

def set_base_dir(server_version: Version):
    global base_dir
    base_dir = BASEDIR
    if server_version == Version.LOWER:
        base_dir = PXC_LOWER_BASE
    elif server_version == Version.HIGHER:
        base_dir = PXC_UPPER_BASE

def get_workdir(worker_id: int):
    if worker_id > 0:
        return global_workdir + '/w' + str(worker_id)
    else:
        return global_workdir

def node_conf(worker_id: int, node_number: int):
    return os.path.join(get_workdir(worker_id), 'conf', 'node' + str(node_number) + '.cnf')

def node_datadir(worker_id: int, node_number: int):
    return os.path.join(get_workdir(worker_id), 'node' + str(node_number))

def node_startup_script(worker_id: int, node_number: int):
    return os.path.join(get_workdir(worker_id), 'log', 'startup' + str(node_number) + '.sh')

def node_socket(worker_id: int, node_number: int):
    return os.path.join(get_workdir(worker_id), 'node' + str(node_number), 'mysql.sock')

def node_err_log(worker_id: int, node_number: int):
    return os.path.join(get_workdir(worker_id), 'log', 'node' + str(node_number) + '.err')

def get_backup_dir(worker_id: int):
    return os.path.join(get_workdir(worker_id), 'backup')

def get_keyring_dir(worker_id: int):
    return os.path.join(get_workdir(worker_id), 'keyring')

def component_keyring_file_path(worker_id: int, node_number: int):
    keyring_dir = get_keyring_dir(worker_id)
    os.makedirs(keyring_dir, exist_ok=True)
    return os.path.join(keyring_dir, node_keyring_file_name.format(node_number=node_number))

def cluster_keyring_file_path(worker_id: int):
    keyring_dir = get_keyring_dir(worker_id)
    os.makedirs(keyring_dir, exist_ok=True)
    return os.path.join(keyring_dir, cluster_keyring_file_name)

def setup_global_keyring(worker_id: int):
    with open(os.path.join(base_dir, 'bin', 'mysqld.my'), 'w') as manifest_file:
        json.dump({"components": "file://" + comp_name}, manifest_file, indent=2)
        manifest_file.write('\n')
    with open(os.path.join(base_dir, 'lib', 'plugin', comp_name + '.cnf'), 'w') as cnf_file:
        json.dump({"path": cluster_keyring_file_path(worker_id), "read_only": False}, cnf_file, indent=2)
        cnf_file.write('\n')

def setup_local_keyring_redirect():
    """Per-table encryption can use local manifest/config files in the datadir."""
    with open(os.path.join(base_dir, 'bin', 'mysqld.my'), 'w') as manifest_file:
        json.dump({"read_local_manifest": True}, manifest_file, indent=2)
        manifest_file.write('\n')
    with open(os.path.join(base_dir, 'lib', 'plugin', comp_name + '.cnf'), 'w') as cnf_file:
        json.dump({"read_local_config": True}, cnf_file, indent=2)
        cnf_file.write('\n')

def setup_local_keyring(worker_id: int, node_number: int):
    with open(os.path.join(node_datadir(worker_id, node_number), 'mysqld.my'), 'w') as manifest_file:
        json.dump({"components": "file://" + comp_name}, manifest_file, indent=2)
        manifest_file.write('\n')

    with open(os.path.join(node_datadir(worker_id, node_number), comp_name + '.cnf'), 'w') as cnf_file:
        json.dump({"path": component_keyring_file_path(worker_id, node_number), "read_only": False}, cnf_file, indent=2)
        cnf_file.write('\n')


class StartCluster:
    def __init__(self, number_of_nodes, debug, server_version: Version = None, worker_id: int = 0):
        self.__number_of_nodes = int(number_of_nodes)
        self.__debug = debug
        self.__worker_id = worker_id
        self.__workdir = get_workdir(worker_id)
        if not os.path.exists( self.__workdir):
            os.mkdir(self.__workdir)
        if Version is not None:
            set_base_dir(server_version)
        self.__workdir_custom_cnf = os.path.join(self.__workdir, 'conf', 'custom.cnf')
        self.__workdir_encryption_cnf = os.path.join(self.__workdir, 'conf', 'encryption.cnf')

    def init_log(self, node_number: int):
        return os.path.join(self.__workdir, 'log', 'init' + str(node_number) + '.log')


    def add_conf(self, option_values: dict):
        cnf_name = open(self.__workdir_custom_cnf, 'a+')
        for opt in option_values:
            cnf_name.write(opt + '=' + option_values[opt] + '\n')
        cnf_name.close()

    def kill_mysqld(self):
        # kill existing mysqld process
        os.system("ps -ef | grep '" + os.path.join(self.__workdir, 'conf', 'node[0-9].cnf') + "' | grep -v grep | "
                                                "awk '{print $2}' | xargs kill -9 >/dev/null 2>&1")

    def sanity_check(self):
        """ Sanity check method will remove existing
            cluster data directories and forcefully kill
            running mysqld processes. This will also check
            the availability of mysqld binary file.
        """
        result = 0
        # kill existing mysqld process
        self.kill_mysqld()

        if not os.path.exists( os.path.join(self.__workdir, 'log')):
            os.mkdir( os.path.join(self.__workdir, 'log'))

        if not os.path.exists( os.path.join(self.__workdir, 'conf')):
            os.mkdir( os.path.join(self.__workdir, 'conf'))

        if not os.path.isfile(os.path.join(base_dir, 'bin', 'mysqld')):
            print(os.path.join(base_dir, 'bin', 'mysqld') + ' does not exist')
            result = 1
        utility_cmd = utility.Utility(self.__debug)
        utility_cmd.check_testcase(result, "Startup sanity check")

    def create_config(self, wsrep_extra, wsrep_provider_option=None, set_admin_address: bool = False,
                      custom_conf_settings: dict = None, default_encryption_conf: bool = True):
        """ Method to create cluster configuration file
            based on the node count. To create configuration
            file it will take default values from conf/pxc.cnf.
            For customised configuration please add your values
            in conf/custom.conf.
        """
        if wsrep_provider_option is None:
            wsrep_provider_option = ''
        version = Utility.version_check(base_dir)
        port_allocations = []
        addr_list = ''
        result = 0
        for j in range(1, self.__number_of_nodes + 1):
            ports = pxc_allocate_ports(self.__worker_id, j, set_admin_address)
            port_allocations.append(ports)
            addr_list = addr_list + '127.0.0.1:' + str(ports[1]) + ','
        if not os.path.isfile(default_pxc_cnf):
            print('Default pxc.cnf is missing in ' + default_pxc_cnf)
            result = 1
        else:
            shutil.copy(default_custom_cnf, self.__workdir_custom_cnf)
        if wsrep_extra == 'encryption' and default_encryption_conf:
            shutil.copy(encryption_cnf, self.__workdir_encryption_cnf)
            if int(version) < int("080024"):
                with open(self.__workdir_encryption_cnf, 'a+') as cnf_file:
                    cnf_file.write('early-plugin-load = keyring_file.so\n')
                    cnf_file.write('keyring_file_data = keyring\n')
        for i in range(1, self.__number_of_nodes + 1):
            cnf = node_conf(self.__worker_id, i)
            shutil.copy(default_pxc_cnf, cnf)
            cnf_name = open(cnf, 'a+')
            if self.__worker_id > 0:
                cnf_name.write('innodb_use_native_aio=0\n')
            if self.__debug == 'YES':
                cnf_name.write('wsrep-debug=1\n')
            cnf_name.write('wsrep_cluster_address=gcomm://' + addr_list + '\n')
            # Calling version check method to compare the version to
            # add wsrep_sst_auth variable. This variable does not
            # required starting from PXC-8.x
            if int(version) < int("080000"):
                cnf_name.write('wsrep_sst_auth=root:\n')
            if int(version) > int("050700"):
                cnf_name.write('log_error_verbosity=3\n')
            mysql_port, galera_port, ist_port, sst_port = port_allocations[i - 1][:4]
            if set_admin_address:
                admin_port = port_allocations[i - 1][4]
            else:
                admin_port = None
            cnf_name.write('port=' + str(mysql_port) + '\n')
            cnf_name.write('wsrep_sst_receive_address=127.0.0.1:' + str(sst_port) + '\n')
            if wsrep_extra == "ssl" or wsrep_extra == "encryption":
                cnf_name.write("wsrep_provider_options='gmcast.listen_addr=tcp://127.0.0.1:"
                               + str(galera_port) + ';ist.recv_addr=127.0.0.1:' + str(ist_port) + ';'
                               + wsrep_provider_option + 'socket.ssl_key='
                               + self.__workdir + '/cert/server-key.pem;socket.ssl_cert='
                               + self.__workdir + '/cert/server-cert.pem;socket.ssl_ca='
                               + self.__workdir + "/cert/ca.pem'\n")
                cnf_name.write('!include ' + self.__workdir + '/conf/ssl.cnf\n')
                sanity.create_ssl_certificate(self.__workdir)
            else:
                cnf_name.write("wsrep_provider_options='gmcast.listen_addr=tcp://127.0.0.1:"
                               + str(galera_port) + ';ist.recv_addr=127.0.0.1:' + str(ist_port) + ';'
                               + wsrep_provider_option + "'\n")
            cnf_name.write('socket=' + node_socket(self.__worker_id, i) + '\n')
            cnf_name.write('server_id=' + str(10 + i) + '\n')
            cnf_name.write('!include ' + self.__workdir_custom_cnf + '\n')
            if default_encryption_conf:
                if wsrep_extra == 'encryption':
                    cnf_name.write('!include ' + self.__workdir_encryption_cnf + '\n')
                    cnf_name.write('pxc_encrypt_cluster_traffic = ON\n')
                elif int(version) > int("050700"):
                    cnf_name.write('pxc_encrypt_cluster_traffic = OFF\n')
            if admin_port is not None:
                cnf_name.write('admin_address=127.0.0.1\n')
                cnf_name.write('admin_port=' + str(admin_port) + '\n')
            if self.__worker_id > 0:
                cnf_name.write('[sst]\ndonor_timeout_wait_joiner=400\n')
            cnf_name.close()
        if custom_conf_settings is not None:
            self.add_conf(custom_conf_settings)
        utility_cmd = utility.Utility(self.__debug)
        utility_cmd.check_testcase(result, "Configuration file creation")

    def add_myextra_configuration(self, config_file):
        """ Adding extra configurations
            based on the testcase
        """
        result = 0
        if not os.path.isfile(config_file):
            print('Custom config ' + config_file + ' is missing')
            result = 1
        config_file = config_file
        cnf_name = open(self.__workdir_custom_cnf, 'a+')
        cnf_name.write('\n')
        cnf_name.write('!include ' + config_file + '\n')
        cnf_name.close()
        utility_cmd = utility.Utility(self.__debug)
        utility_cmd.check_testcase(result, "PXC: Adding custom configuration")

    def initialize_cluster(self, init_extra=None, encryption=False, sys_table_encrypt=False):
        """ Method to initialize the cluster database
            directories. This will initialize the cluster
            using --initialize-insecure option for
            passwordless authentication.
        """
        result = ""
        if init_extra is None:
            init_extra = ''
        # This is for encryption testing. Encryption features are not fully supported
        # if wsrep_extra == "encryption":
        #    init_opt = '--innodb_undo_tablespaces=2 '

        version = Utility.version_check(base_dir)

        if encryption:
            if sys_table_encrypt:
                init_extra = init_extra + " --innodb_sys_tablespace_encrypt=ON"
                if int(version) < int("080024"):
                    init_extra = init_extra + " --early-plugin-load=keyring_file.so --keyring_file_data=keyring"
                else:
                    setup_global_keyring(self.__worker_id)
            elif int(version) >= int("080024"):
                setup_local_keyring_redirect()

        for i in range(1, self.__number_of_nodes + 1):
            conf = node_conf(self.__worker_id, i)
            datadir = node_datadir(self.__worker_id, i)
            initialize_log = self.init_log(i)
            if os.path.exists(datadir):
                os.system('rm -rf ' + datadir + '>/dev/null 2>&1')
            if not os.path.isfile(conf):
                print('Could not find config file ' + conf)
                exit(1)
            if int(version) < int("050700"):
                os.mkdir(datadir)
                initialize_node = (base_dir + '/scripts/mysql_install_db --no-defaults --basedir=' + base_dir +
                                   ' --datadir=' + datadir + ' > ' + initialize_log + ' 2>&1')
            else:
                initialize_node = (base_dir + '/bin/mysqld --no-defaults --initialize-insecure ' + init_extra +
                                   ' --basedir=' + base_dir + ' --datadir=' + datadir + ' > ' + initialize_log +
                                   ' 2>&1')
            if self.__debug == 'YES':
                print(initialize_node)
            run_query = subprocess.call(initialize_node, shell=True, stderr=subprocess.DEVNULL)
            result = ("{}".format(run_query))
            if encryption and not sys_table_encrypt:
                if int(version) >= int("080024"):
                    setup_local_keyring(self.__worker_id, i)

        utility_cmd = utility.Utility(self.__debug)
        utility_cmd.check_testcase(int(result), "Initializing cluster")

    def start_cluster(self, my_extra=None, terminate_on_startup_failure: bool = True):
        """ Method to start the cluster nodes. This method
            will also check the startup status.
        """
        result = 1
        if my_extra is None:
            my_extra = ''
        pxc_nodes = []
        for i in range(1, self.__number_of_nodes + 1):
            socket = node_socket(self.__worker_id, i)
            conf = node_conf(self.__worker_id, i)
            err_log = node_err_log(self.__worker_id, i)
            mysqld = base_dir + '/bin/mysqld'
            datadir = node_datadir(self.__worker_id, i)
            startup_script = node_startup_script(self.__worker_id, i)

            startup = (mysqld + ' --defaults-file=' + conf +
                       ' --datadir=' + datadir +
                       ' --basedir=' + base_dir + ' ' + my_extra +
                       ' --wsrep-provider=' + base_dir + '/lib/libgalera_smm.so')
            if i == 1:
                startup = startup + ' --wsrep-new-cluster'
            startup = startup + ' --log-error=' + err_log + ' > ' + err_log + ' 2>&1'

            save_startup = 'echo "' + startup + '" > ' + startup_script
            os.system(save_startup)
            if self.__debug == 'YES':
                print(startup)
            launch_result = launch_server(startup)
            if launch_result != 0:
                print("Node" + str(i) + " startup failed on launch with exit code " + str(launch_result))
                result = -2
                break
            utility_cmd = utility.Utility(self.__debug)
            node = db_connection.DbConnection(user=user, socket=socket, node_num=i, data_dir=datadir, conf_file=conf,
                                              err_log=err_log, base_dir=base_dir, startup_script=startup_script,
                                              debug=self.__debug, worker_id=self.__worker_id)
            result = utility_cmd.startup_check(node, terminate_on_startup_failure)
            pxc_nodes.append(node)
        if result != 0:
            return []
        return pxc_nodes

    @staticmethod
    def join_new_node(donor: DbConnection, joiner_node_number: int, basedir: str = base_dir, debug: str = 'NO', encryption: bool = False):
        worker_id = donor.get_worker_id()   
        joiner_node_cnf = node_conf(worker_id, joiner_node_number)
        startup_script = node_startup_script(worker_id, joiner_node_number)
        joiner_data_dir = node_datadir(worker_id, joiner_node_number)
        donor_node_num = donor.get_node_number()
        shutil.copy(donor.get_conf_file(), joiner_node_cnf)
        wsrep_cluster_addr = donor.execute_get_row("show variables like 'wsrep_cluster_address'")[1]

        port_no, wsrep_port_no, ist_port_no, sst_port_no = pxc_allocate_ports(
            worker_id, joiner_node_number)
        os.system("sed -i 's#node" + str(donor_node_num) + "#node" + str(joiner_node_number) + "#g' " + joiner_node_cnf)
        os.system("sed -i '/wsrep_sst_auth=root:/d' " + joiner_node_cnf)
        os.system("sed -i  '0,/^[ \\t]*wsrep_cluster_address[ \\t]*=.*$/s|"
                  "^[ \\t]*wsrep_cluster_address[ \\t]*=.*$|wsrep_cluster_address="
                  + wsrep_cluster_addr + "127.0.0.1:" + str(wsrep_port_no) + "|' "
                  + joiner_node_cnf)
        os.system("sed -i  '0,/^[ \\t]*port[ \\t]*=.*$/s|"
                  "^[ \\t]*port[ \\t]*=.*$|port="
                  + str(port_no) + "|' " + joiner_node_cnf)
        os.system(
            f"sed -i '/^[ \\t]*wsrep_provider_options/s#"
            f"gmcast\\.listen_addr=tcp://127\\.0\\.0\\.1:[0-9][0-9]*#"
            f"gmcast.listen_addr=tcp://127.0.0.1:{wsrep_port_no}#' "
            f"{joiner_node_cnf}"
        )
        os.system(
            f"sed -i '/^[ \\t]*wsrep_provider_options/s#"
            f"ist\\.recv_addr=127\\.0\\.0\\.1:[0-9][0-9]*#"
            f"ist.recv_addr=127.0.0.1:{ist_port_no}#' "
            f"{joiner_node_cnf}"
        )
        os.system("sed -i  '0,/^[ \\t]*wsrep_sst_receive_address[ \\t]*=.*$/s|"
                  "^[ \\t]*wsrep_sst_receive_address[ \\t]*=.*$|wsrep_sst_receive_address=127.0.0.1:"
                  + str(sst_port_no) + "|' " + joiner_node_cnf)
        os.system("sed -i  '0,/^[ \\t]*server_id[ \\t]*=.*$/s|"
                  "^[ \\t]*server_id[ \\t]*=.*$|server_id="
                  "14|' " + joiner_node_cnf)

        create_upgrade_startup = (
                'sed  "s#' + lower_base_dir + '#' + basedir + '#g" ' + donor.get_startup_script() +
                ' > ' + startup_script)
        if debug == 'YES':
            print(create_upgrade_startup)
        os.system(create_upgrade_startup)
        os.system("sed -i 's#node" + str(donor_node_num) +
                  "#node" + str(joiner_node_number) + "#g' " + startup_script)
        os.system("rm -rf " + joiner_data_dir)
        os.mkdir(joiner_data_dir)
        if encryption:
            setup_local_keyring(worker_id, joiner_node_number)

        time.sleep(10)
        joiner = db_connection.DbConnection(user=user, socket=node_socket(worker_id, joiner_node_number),
                                            node_num=joiner_node_number, data_dir=joiner_data_dir,
                                            conf_file=joiner_node_cnf, err_log=node_err_log(worker_id, joiner_node_number),
                                            base_dir=base_dir, startup_script=startup_script, debug=debug, worker_id=worker_id)
        utility_cmd = utility.Utility(debug)
        utility_cmd.restart_cluster_node(joiner)
        utility_cmd.startup_check(joiner)
        utility_cmd.wait_for_wsrep_status(joiner)

        return joiner

    @staticmethod
    def join_new_upgraded_node(donor: DbConnection, joiner_node_number: int, debug: str = 'NO', encryption: bool = False):
        return StartCluster.join_new_node(donor, joiner_node_number, higher_version_basedir, debug, encryption)

    @staticmethod
    def upgrade_pxc_node(node: DbConnection, debug, node_to_add_load: DbConnection = None, config_replace: dict = None,
                         node_sync_timeout: int = DEFAULT_SERVER_UP_TIMEOUT):
        node.shutdown()
        time.sleep(60)

        if node_to_add_load is not None:
            sysbench = sysbench_run.SysbenchRun(node_to_add_load, debug,
                                                get_workdir(node_to_add_load.get_worker_id()))
            sysbench.sanity_check('test_one')
            sysbench.sanity_check('test_two')
            sysbench.sanity_check('test_three')
            sysbench.test_sysbench_load('test_one', SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                        SYSBENCH_LOAD_TEST_TABLE_SIZE)
            sysbench.test_sysbench_load('test_two', SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                        SYSBENCH_LOAD_TEST_TABLE_SIZE)
            sysbench.test_sysbench_load('test_three', SYSBENCH_TABLE_COUNT, SYSBENCH_THREADS,
                                        SYSBENCH_LOAD_TEST_TABLE_SIZE)

        utility_cmd = utility.Utility(debug)
        version = utility_cmd.version_check(PXC_UPPER_BASE)
        if int(version) > int("080000"):
            os.system("sed -i '/wsrep_sst_auth=root:/d' " + node.get_conf_file())
            if config_replace is not None:
                for cnf in config_replace:
                    os.system("sed -i 's#" + cnf + "=.*#" + cnf + "=" + config_replace[cnf] + "#g' " +
                              node.get_conf_file())
            startup_cmd = (higher_version_basedir + '/bin/mysqld --defaults-file=' + node.get_conf_file() +
                           ' --wsrep-provider=' + higher_version_basedir + '/lib/libgalera_smm.so --datadir='
                           + node.get_data_dir() + ' --basedir=' + higher_version_basedir + ' --log-error=' +
                           node.get_error_log() + ' >> ' + node.get_error_log() + ' 2>&1')
            utility_cmd.check_testcase(0, "Starting cluster node with upgraded version")
        else:
            startup_cmd = (higher_version_basedir + '/bin/mysqld --defaults-file=' + node.get_conf_file() +
                           ' --datadir=' + node.get_data_dir() + ' --basedir=' + higher_version_basedir +
                           ' --wsrep-provider=none --log-error=' + node.get_error_log() +
                           ' >> ' + node.get_error_log() + ' 2>&1')
        if debug == 'YES':
            print(startup_cmd)
        launch_result = launch_server(startup_cmd)
        if launch_result != 0:
            print("Cluster node" + str(node.get_node_number()) + " startup failed on launch with exit code "
                  + str(launch_result))
            utility_cmd.check_testcase(launch_result, "Starting cluster node with upgraded version")
            return
        utility_cmd.startup_check(node)
        utility_cmd.wait_for_wsrep_status(node, node_sync_timeout)
        if int(version) < int("080000"):
            upgrade_cmd = (higher_version_basedir + '/bin/mysql_upgrade -uroot --socket=' + node.get_socket() + ' > '
                           + node.get_error_log() + ' 2>&1')
            if debug == 'YES':
                print(upgrade_cmd)
            result = os.system(upgrade_cmd)
            utility_cmd.check_testcase(result, "Cluster node" + str(node.get_node_number()) + " upgrade is successful")
            node.shutdown()
            time.sleep(30)
            utility_cmd.check_testcase(0, "Shutdown cluster node" + str(node.get_node_number()) + " after upgrade run")
            create_startup = ('sed -i  "s#' + lower_base_dir + '#' + higher_version_basedir + '#g" ' + node.get_startup_script())
            if debug == 'YES':
                print(create_startup)
            os.system(create_startup)
            if int(node.get_node_number()) == 1:
                remove_bootstrap_option = 'sed -i "s#--wsrep-new-cluster##g" ' + node.get_startup_script()
                if debug == 'YES':
                    print(remove_bootstrap_option)
                os.system(remove_bootstrap_option)
            time.sleep(5)

            utility_cmd.restart_cluster_node(node)
            utility_cmd.startup_check(node)
            utility_cmd.wait_for_wsrep_status(node)


    
    def pxb_sanity_check(node: DbConnection, version: str):
        """ This method will check pxb installation and
            cleanup backup directory
        """
        # Check xtrabackup installation
        if find_executable('xtrabackup') is None:
            print('\tERROR! Percona Xtrabackup is not installed.')
            exit(1)

        backup_dir = get_backup_dir(node.get_worker_id())
        # Recreate backup directory
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        os.mkdir(backup_dir)

        # Check PXC version and create XB user.
        if int(version) < int("050700"):
            queries = ["create user 'xbuser'@'localhost' identified by 'test'",
                       "grant all on *.* to xbuser'@'localhost'"]
        else:
            queries = ["create user 'xbuser'@'localhost' identified by 'test'",
                       "grant all on *.* to 'xbuser'@'localhost'"]
        node.execute_queries(queries)
        
    @staticmethod
    def pxb_backup(node: DbConnection, encryption: bool, copy_back_to_ps_node: bool = False, debug: str = 'NO'):
        """ This method will backup PXC/PS data directory
            with the help of xtrabackup.
        """
        worker_id = node.get_worker_id()
        workdir = get_workdir(worker_id)
        backup_dir = get_backup_dir(worker_id)
        # Enable keyring file plugin if it is encryption run
        backup_extra = ''
        prepare_extra = ''
        if encryption:
            version_info = node.get_mysql_version()
            version = "{:02d}{:02d}{:02d}".format(int(version_info.split('.')[0]),
                                                  int(version_info.split('.')[1]),
                                                  int(version_info.split('.')[2].split('-')[0]))
            if int(version) < int("080024"):
                backup_extra = " --keyring-file-data=" + node.get_data_dir() + \
                           "/keyring --early-plugin-load='keyring_file=keyring_file.so'"
            else:
                prepare_extra = " --component-keyring-config=" + node.get_data_dir() + '/' + comp_name + '.cnf'
        def run_with_timeout(cmd, description):
            try:
                return subprocess.call(cmd, shell=True, timeout=BACKUP_TIMEOUT)
            except subprocess.TimeoutExpired as timeout_error:
                print(description + " timed out after " + str(BACKUP_TIMEOUT) + " seconds: "
                      + str(timeout_error))
                return -1
            except Exception as backup_error:
                print(description + " failed with exception: " + str(backup_error))
                return -2

        # Backup data using xtrabackup
        backup_cmd = ("xtrabackup --user=xbuser --password='test' --backup --target-dir=" + backup_dir +
                      " -S" + node.get_socket() + " --datadir=" + node.get_data_dir() + " " +
                      backup_extra + " --lock-ddl >" + workdir + "/log/xb_backup.log 2>&1")
        if debug == 'YES':
            print(backup_cmd)
        result = run_with_timeout(backup_cmd, "xtrabackup backup")
        Utility.check_testcase(result, "xtrabackup backup")

        # Prepare backup for node startup
        prepare_backup = ("xtrabackup --prepare --target_dir=" + backup_dir + ' ' + backup_extra + prepare_extra +
                          " --lock-ddl >" + workdir + "/log/xb_backup_prepare.log 2>&1")
        if debug == 'YES':
            print(prepare_backup)
        result = run_with_timeout(prepare_backup, "xtrabackup prepare")
        Utility.check_testcase(result, "xtrabackup prepare")

        # copy backup directory to destination
        if copy_back_to_ps_node:
            dest_datadir = workdir + '/psnode1'
            if os.path.exists(dest_datadir):
                shutil.rmtree(dest_datadir)
            copy_backup = ("xtrabackup --copy-back --target-dir=" + backup_dir + " --datadir=" + dest_datadir +
                           " " + backup_extra + " --lock-ddl >" +  workdir + "/log/copy_backup.log 2>&1")
            if debug == 'YES':
                print(copy_backup)
            result = run_with_timeout(copy_backup, "xtrabackup copy-back")
            Utility.check_testcase(result, "xtrabackup copy-back")

            # Copy keyring file to destination directory for encryption startup
            if encryption:
                if int(version) >= int("080024"):
                    keyring_dir = get_keyring_dir(worker_id)
                    dest_keyring_file = os.path.join(keyring_dir, ps_node_keyring_file_name.format(node_number=1))
                    shutil.copy(os.path.join(keyring_dir, node_keyring_file_name.format(node_number=1)), dest_keyring_file)
                    with open(os.path.join(dest_datadir, comp_name + '.cnf'), 'w') as cnf_file:
                        json.dump({"path": dest_keyring_file, "read_only": False}, cnf_file, indent=2)
                        cnf_file.write('\n')
                else:
                    os.system("cp " + node.get_data_dir() + "/keyring " + dest_datadir)

        if debug == 'YES':
            print("Backup dir path: ", backup_dir)

        return backup_dir
