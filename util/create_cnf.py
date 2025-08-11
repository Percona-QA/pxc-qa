# This will help us to create cluster cnf on the fly
import os
import shutil
import random

from config import WORKDIR

workdir = WORKDIR

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../'))

pxc_conf = parent_dir + '/conf/pxc.cnf'


def node_conf(node_number: int):
    return workdir + '/conf/node' + str(node_number) + '.cnf'


class CreateCNF:

    def __init__(self, number_of_nodes: int):
        self.__number_of_nodes = number_of_nodes

    def create_config(self):
        """ Method to create cluster configuration file
            based on the node count. To create configuration
            file it will take default values from conf/pxc.cnf.
            For customised configuration please add your values
            in conf/custom.conf.
        """
        port = random.randint(10, 50) * 1001
        port_list = []
        addr_list = ''
        for j in range(1, self.__number_of_nodes + 1):
            port_list += [port + (j * 2)]
            addr_list = addr_list + '127.0.0.1:' + str(port + (j * 2) + 2) + ','
        if not os.path.isfile(pxc_conf):
            print('Default pxc.cnf is missing ' + pxc_conf)
            return 1
        for i in range(1, self.__number_of_nodes + 1):
            shutil.copy(parent_dir + '/conf/pxc.cnf', node_conf(i))
            cnf_name = open(node_conf(i), 'a+')
            cnf_name.write('wsrep_cluster_address=gcomm://' + addr_list + '\n')
            cnf_name.write('port=' + str(port_list[i - 1]) + '\n')
            cnf_name.write("wsrep_provider_options='gmcast.listen_addr=tcp://127.0.0.1:" +
                           str(port_list[i - 1] + 8) + "'\n")
            cnf_name.close()
        return 0


cnf_file = CreateCNF(2)
cnf_file.create_config()
