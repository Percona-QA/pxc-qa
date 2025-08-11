import os
import configparser
from util import utility
from util.db_connection import DbConnection

# Reading initial configuration
config = configparser.ConfigParser()
script_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(script_dir, '../'))
rand_gen_dir = parent_dir + '/randgen'
gen_data_pl = rand_gen_dir + '/gendata.pl'


class RQGDataGen:
    def __init__(self, node: DbConnection, debug):
        self.__node = node
        self.debug = debug
        self.utility_cmd = utility.Utility(debug)
        self.version = self.utility_cmd.version_check(node.get_base_dir())

    def initiate_rqg(self, module, db, work_dir):
        """ Method to initiate RQD data load against
            Percona XtraDB cluster.
        """
        port = self.__node.execute_get_value("select @@port")
        queries = ['drop database if exists ' + db, 'create database ' + db]
        self.__node.execute_queries(queries)
        # Get RQG module
        module = rand_gen_dir + '/conf/' + module
        # Create schema for RQG run

        if int(self.version) > int("050700"):
            queries = ["drop user if exists 'rqg_test'@'%'",
                       "create user rqg_test@'%' identified by ''",
                       "grant all on *.* to rqg_test@'%'"]
            self.__node.execute_queries(queries)

        # Checking RQG module
        os.chdir(rand_gen_dir)
        if not os.path.exists(module):
            print(module + ' does not exist in RQG')
            exit(1)
        # Run RQG
        for file in os.listdir(module):
            if file.endswith(".zz"):
                rqg_command = "perl " + gen_data_pl + \
                              " --dsn=dbi:mysql:host=127.0.0.1:port=" \
                              + str(port) + ":user=" + self.__node.get_user() + ":database=" + db + " --spec=" + \
                              module + '/' + file + " > " + \
                              work_dir + "/log/rqg_run.log 2>&1"
                if self.debug == 'YES':
                    print(rqg_command)
                result = os.system(rqg_command)
                self.utility_cmd.check_testcase(result, "RQG data load (DB: " + db + ")")

    def pxc_dataload(self, work_dir):
        """
            RQG data load for PXC Server
        """
        if int(self.version) < int("050700"):
            rqg_config = ['galera', 'transactions', 'gis', 'runtime', 'temporal']
        else:
            rqg_config = ['galera', 'transactions', 'partitioning', 'gis', 'runtime', 'temporal']
        for conf in rqg_config:
            self.initiate_rqg(conf, 'db_' + conf, work_dir)
