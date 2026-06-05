import argparse
import atexit
import json
import os
import re
import sys

from config import WORKDIR, NODE, PT_BASEDIR, BASEDIR, SERVER, PXC_LOWER_BASE, PXC_UPPER_BASE
from util import pxc_startup, ps_startup
from util.utility import *

workdir = WORKDIR
pt_basedir = PT_BASEDIR
server = SERVER
comp_name = 'component_keyring_file'

# Read argument
parser = argparse.ArgumentParser(prog='PXC test', usage='%(prog)s [options]')
parser.add_argument('-e', '--encryption-run', action='store_true',
                    help='This option will enable encryption options')
parser.add_argument('-d', '--debug', action='store_true',
                    help='This option will enable debug logging')

args, extra_args = parser.parse_known_args()

worker_id = 0
for extra_arg in extra_args:
    if re.fullmatch(r'-[1-9][0-9]*', extra_arg):
        if worker_id != 0:
            parser.error('Only one worker option can be specified')
        worker_id = int(extra_arg[1:])
    else:
        parser.error('unrecognized arguments: ' + extra_arg)

if worker_id > 0:
    workdir = workdir + "/w" + str(worker_id)

tests_log_dir = workdir + "/log" + "/tests_log"
os.makedirs(tests_log_dir, exist_ok=True)
test_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
test_log = open(tests_log_dir + "/" + test_name + ".log", "a", buffering=1)
sys.stdout = test_log
sys.stderr = test_log


def _restore_test_logging():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    test_log.close()


atexit.register(_restore_test_logging)

encryption = args.encryption_run

debug = 'NO'
if args.debug is True:
    debug = 'YES'

utility_cmd = Utility(debug)
utility_cmd.check_python_version()
version = utility_cmd.version_check(BASEDIR)
lower_version = get_mysql_version(PXC_LOWER_BASE)
upper_version = get_mysql_version(PXC_UPPER_BASE)
low_version_num = utility_cmd.version_check(PXC_LOWER_BASE)
high_version_num = utility_cmd.version_check(PXC_UPPER_BASE)
db = "test"


class BaseTest:
    def __init__(self, number_of_nodes: int = int(NODE),
                 wsrep_provider_options=None,
                 my_extra=None,
                 extra_config_file=None,
                 init_extra=None,
                 vers: Version = None,
                 encrypt: bool = False,
                 ssl: bool = False):
        self.__number_of_nodes = number_of_nodes
        self.__my_extra = my_extra
        self.__wsrep_provider_options = wsrep_provider_options
        self.__extra_config_file = extra_config_file
        self.__init_extra = init_extra
        self.__version = vers
        self.encrypt = encrypt
        self.ssl = ssl
        self.pxc_nodes: list[DbConnection] = None
        self.node1: DbConnection = None
        self.node2: DbConnection = None
        self.node3: DbConnection = None
        self.ps_nodes: list[DbConnection] = None
        self._shutdown_registered = False

    def _register_shutdown_on_exit(self):
        if not self._shutdown_registered:
            atexit.register(self._shutdown_on_exit)
            self._shutdown_registered = True

    def _shutdown_on_exit(self):
        if self.pxc_nodes:
            self.shutdown_nodes(self.pxc_nodes)
        if self.ps_nodes:
            self.shutdown_nodes(self.ps_nodes)

    def start_pxc(self, my_extra: str = None, custom_conf_settings: dict = None,
                  terminate_on_startup_failure: bool = True):
        if my_extra is not None:
            my_extra_options = my_extra
        else:
            my_extra_options = self.__my_extra

        # Start PXC cluster
        server_startup = pxc_startup.StartCluster(self.__number_of_nodes, debug, self.__version, worker_id)
        server_startup.sanity_check()
        if encryption or self.encrypt:
            server_startup.create_config('encryption', self.__wsrep_provider_options,
                                         custom_conf_settings=custom_conf_settings)
        elif self.ssl:
            server_startup.create_config('ssl', self.__wsrep_provider_options,
                                         custom_conf_settings=custom_conf_settings)
        else:
            server_startup.create_config('none', self.__wsrep_provider_options,
                                         custom_conf_settings=custom_conf_settings)
        server_startup.initialize_cluster(encryption=encryption or self.encrypt)
        if self.__extra_config_file is not None:
            server_startup.add_myextra_configuration(self.__extra_config_file)
        self.pxc_nodes = server_startup.start_cluster(my_extra_options, terminate_on_startup_failure)
        self._register_shutdown_on_exit()
        if len(self.pxc_nodes) == self.__number_of_nodes:
            self.node1 = self.pxc_nodes[0]
            self.node2 = self.pxc_nodes[1]
            self.node3 = self.pxc_nodes[2]
            self.node1.test_connection_check()
        else:
            print("Some problem while setting up cluster nodes. Not all nodes seems in healthy state")
            print("Number of nodes: " + str(len(self.pxc_nodes)))
            if terminate_on_startup_failure:
                exit(1)
        if debug == 'YES':
            for node in self.pxc_nodes:
                print("node is " + node.get_socket())

    def start_ps(self, my_extra=None):
        """ Start Percona Server. This method will
            perform sanity checks for PS startup
        """
        # Start PXC cluster for replication test
        if my_extra is not None:
            my_extra_options = my_extra
        else:
            my_extra_options = self.__my_extra
        server_startup = ps_startup.StartPerconaServer(self.__number_of_nodes, debug, self.__version, worker_id)
        server_startup.test_sanity_check()
        if encryption or self.encrypt:
            server_startup.create_config('encryption')
        else:
            server_startup.create_config()
        server_startup.initialize_server(encryption=encryption or self.encrypt)
        if self.__extra_config_file is not None:
            server_startup.add_myextra_configuration(self.__extra_config_file)
        self.ps_nodes = server_startup.start_server(my_extra_options)
        if self.ps_nodes:
            self._register_shutdown_on_exit()

    def shutdown_nodes(self, nodes=None):
        if nodes is None:
            nodes = self.pxc_nodes
        for node in nodes:
            node.shutdown()

    def set_extra_conf_file(self, conf_file):
        self.__extra_config_file = conf_file

    def set_wsrep_provider_options(self, options):
        self.__wsrep_provider_options = options

    def set_number_of_nodes(self, number_of_nodes: int):
        self.__number_of_nodes = number_of_nodes

    def get_number_of_nodes(self):
        return self.__number_of_nodes
