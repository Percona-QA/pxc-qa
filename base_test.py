import argparse

from config import WORKDIR, NODE, PT_BASEDIR, BASEDIR, SERVER, PXC_LOWER_BASE, PXC_UPPER_BASE
from util import pxc_startup, ps_startup
from util.utility import *

workdir = WORKDIR
pt_basedir = PT_BASEDIR
server = SERVER

# Read argument
parser = argparse.ArgumentParser(prog='PXC test', usage='%(prog)s [options]')
parser.add_argument('-e', '--encryption-run', action='store_true',
                    help='This option will enable encryption options')
parser.add_argument('-d', '--debug', action='store_true',
                    help='This option will enable debug logging')

args = parser.parse_args()
encryption = 'NO'
if args.encryption_run is True:
    encryption = 'YES'

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

    def start_pxc(self, my_extra: str = None, custom_conf_settings: dict = None,
                  terminate_on_startup_failure: bool = True):
        if my_extra is not None:
            my_extra_options = my_extra
        else:
            my_extra_options = self.__my_extra

        # Start PXC cluster for ChaosMonkey test
        server_startup = pxc_startup.StartCluster(self.__number_of_nodes, debug, self.__version)
        server_startup.sanity_check()
        if encryption == 'YES' or self.encrypt:
            server_startup.create_config('encryption', self.__wsrep_provider_options,
                                         custom_conf_settings=custom_conf_settings)
        elif self.ssl:
            server_startup.create_config('ssl', self.__wsrep_provider_options,
                                         custom_conf_settings=custom_conf_settings)
        else:
            server_startup.create_config('none', self.__wsrep_provider_options,
                                         custom_conf_settings=custom_conf_settings)
        server_startup.initialize_cluster()
        if self.__extra_config_file is not None:
            server_startup.add_myextra_configuration(self.__extra_config_file)
        self.pxc_nodes = server_startup.start_cluster(my_extra_options, terminate_on_startup_failure)
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
        # atexit.register(shutdown_nodes(self.node))

    def start_ps(self, my_extra=None):
        """ Start Percona Server. This method will
            perform sanity checks for PS startup
        """
        # Start PXC cluster for replication test
        if my_extra is not None:
            my_extra_options = my_extra
        else:
            my_extra_options = self.__my_extra
        server_startup = ps_startup.StartPerconaServer(self.__number_of_nodes, debug, self.__version)
        server_startup.test_sanity_check()
        if encryption == 'YES':
            server_startup.create_config('encryption')
        else:
            server_startup.create_config()
        server_startup.initialize_server()
        if self.__extra_config_file is not None:
            server_startup.add_myextra_configuration(self.__extra_config_file)
        self.ps_nodes = server_startup.start_server(my_extra_options)

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
