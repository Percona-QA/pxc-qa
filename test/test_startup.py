import configparser
import unittest
from util import db_connection, pxc_startup

config = configparser.ConfigParser()
config.read('config.ini')
config.sections()

cluster = pxc_startup.StartCluster(3, 'YES')
pxc_nodes = []

class TestStartup(unittest.TestCase):

    def test_01_sanity_check(self):
        self.assertEqual(cluster.sanity_check(), 0,
                         'work/base directory have some issues')
        print('PXC Sanity check')

    def test_02_initialize_cluster(self):
        cluster.create_config()
        self.assertIsNot(cluster.initialize_cluster(), 1,
                         'Could not initialize database directory. '
                         'Please check error log')

    def test_03_start_cluster(self):
        global pxc_nodes
        pxc_nodes = cluster.start_cluster()
        if len(pxc_nodes) == 0:
            self.fail('Could not start cluster, '
                      'Please check error log')
        print('Started Cluster')

    def test_04_connection_check(self):
        global pxc_nodes
        if len(pxc_nodes) == 0:
            self.skipTest('No nodes to check connection')
        for node in pxc_nodes:
            self.assertEqual(node.connection_check() , 0,
                         'Could not establish DB connection')
        print('Checked DB connection')


if __name__ == '__main__':
    unittest.main()
