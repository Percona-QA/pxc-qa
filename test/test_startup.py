import configparser
import unittest
from util import db_connection, pxc_startup

config = configparser.ConfigParser()
config.read('config.ini')
config.sections()
workdir = config['config']['workdir']
basedir = config['config']['basedir']

cluster = pxc_startup.StartCluster(3, 'YES')
connection_check = db_connection.DbConnection(user='root', socket='/tmp/node1.sock')
connection_check.connection_check()


class TestStartup(unittest.TestCase):

    def test_sanity_check(self):
        self.assertEqual(cluster.sanity_check(), 0,
                         'work/base directory have some issues')
        print('PXC Sanity check')

    def test_initialize_cluster(self):
        self.assertIsNot(cluster.initialize_cluster(), 1,
                         'Could not initialize database directory. '
                         'Please check error log')

    def test_start_cluster(self):
        self.assertIsNot(cluster.start_cluster(), 1,
                         'Could not start cluster, '
                         'Please check error log')
        print('Started Cluster')

    def test_connection_check(self):
        self.assertIsNot(connection_check.connection_check(), 1,
                         'Could not establish DB connection')
        print('Checked DB connection')


if __name__ == '__main__':
    unittest.main()
