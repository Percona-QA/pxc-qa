import os

from util import utility
from util.db_connection import DbConnection


class TableChecksum:
    def __init__(self, node: DbConnection, workdir, pt_basedir, debug):
        self.__workdir = workdir
        self.__pt_basedir = pt_basedir
        self.__node = node
        self.__debug = debug
        self.__utility_cmd = utility.Utility(debug)

    def sanity_check(self, nodes: list[DbConnection]):
        """ Sanity check method will check
            the availability of pt-table-checksum
            binary file.
        """
        if not os.path.isfile(self.__pt_basedir + '/bin/pt-table-checksum'):
            print('pt-table-checksum is missing in percona toolkit basedir')
            return 1

        version = self.__utility_cmd.version_check(self.__node.get_socket())

        queries = ["create user if not exists pt_user@'localhost' identified by 'test'",
                   "grant all on *.* to pt_user@'localhost'"]

        # Creating pt_user for database consistency check
        if int(version) < int("050700"):
            queries[0] = "create user pt_user@'localhost' identified by 'test'"
        self.__node.execute_queries(queries)

        queries = ["drop database if exists percona",
                   "create database percona",
                   "create table percona.dsns(id int, parent_id int, dsn varchar(100), primary key(id))"]
        # Creating percona db for cluster data checksum
        self.__node.execute_queries(queries)

        for node in nodes:
            self.__node.execute('insert into percona.dsns (id,dsn) values (' + str(node.get_port()) + ",'h=127.0.0.1,P="
                                + str(node.get_port()) + ",u=pt_user,p=test')")
        return 0

    def error_status(self, error_code):
        # Checking pt-table-checksum error
        error_map = {'1': ": A non-fatal error occurred", '2': ": --pid file exists and the PID is running",
                     '4': ": Caught SIGHUP, SIGINT, SIGPIPE, or SIGTERM",
                     '8': ": No replicas or cluster nodes were found", '16': ": At least one diff was found",
                     '32': ": At least one chunk was skipped", '64': ": At least one table was skipped", }
        if error_code == "0":
            self.__utility_cmd.check_testcase(0, "pt-table-checksum run status")
        else:
            msg = error_map.get(error_code)
            if msg is None:
                msg = ": Fatal error occurred. Please check error log for more info"

            self.__utility_cmd.check_testcase(1, "pt-table-checksum error code " + msg)

    def data_consistency(self, database):
        """ Data consistency check
            method will compare the
            data between cluster nodes
        """
        port = self.__node.execute_get_value("select @@port")
        version = self.__utility_cmd.version_check(self.__node.get_base_dir())
        # Disable pxc_strict_mode for pt-table-checksum run
        if int(version) > int("050700"):
            self.__node.execute("set global pxc_strict_mode=DISABLED")

        run_checksum = self.__pt_basedir + "/bin/pt-table-checksum h=127.0.0.1,P=" + \
                       str(port) + ",u=pt_user,p=test -d" + database + \
                       " --recursion-method dsn=h=127.0.0.1,P=" + str(port) + \
                       ",u=pt_user,p=test,D=percona,t=dsns >" + self.__workdir + "/log/pt-table-checksum.log 2>&1; echo $?"
        checksum_status = os.popen(run_checksum).read().rstrip()
        self.error_status(checksum_status)
        if int(version) > int("050700"):
            # Enable pxc_strict_mode after pt-table-checksum run
            self.__node.execute("set global pxc_strict_mode=ENFORCING")
        return 0
