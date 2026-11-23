"""Unit tests for Utility.test_table_count that need no running server.

Run from the repository root (config.py reads ./config.ini):
    python3 test/test_table_checksum.py
(`python3 -m unittest test.…` can pick up Python's own `test` package instead.)
"""
import io
import os
import sys
import types
import unittest
from unittest import mock

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../'))
sys.path.insert(0, parent_dir)

# util.db_connection imports mysql.connector at module level. These tests
# never connect, so stub it when the connector isn't installed locally.
try:
    import mysql.connector  # noqa: F401
except ImportError:
    mysql_module = types.ModuleType('mysql')
    connector_module = types.ModuleType('mysql.connector')
    connector_module.errors = types.ModuleType('mysql.connector.errors')
    mysql_module.connector = connector_module
    native_module = types.ModuleType('_mysql_connector')
    native_module.MySQLInterfaceError = type('MySQLInterfaceError', (Exception,), {})
    sys.modules.update({'mysql': mysql_module, 'mysql.connector': connector_module,
                        'mysql.connector.errors': connector_module.errors,
                        '_mysql_connector': native_module})

from util.utility import Utility  # noqa: E402


class FakeNode:
    """Answers SHOW TABLES and CHECKSUM TABLE like a server would."""

    def __init__(self, checksums, node_number=0):
        self.checksums = checksums
        self.node_number = node_number

    def get_node_number(self):
        return self.node_number

    def execute_get_values(self, query):
        if query.lower().startswith('show full tables in'):
            assert query.endswith("where Table_type = 'BASE TABLE'"), query
            return [(table, 'BASE TABLE') for table in self.checksums]
        if query.lower().startswith('checksum table'):
            table = query.split('.')[-1].strip('`')
            db = query.split()[2].split('.')[0].strip('`')
            return [(db + '.' + table, self.checksums.get(table))]
        raise AssertionError('unexpected query: ' + query)

    def execute_get_value(self, query, retries=0, retry_wait=5):
        # Mirrors DbConnection.execute_get_value: first column of the first row.
        return self.execute_get_values(query)[0][0]


class TestTableCount(unittest.TestCase):

    def run_check(self, checksums1, checksums2):
        utility = Utility('NO')
        with mock.patch('util.utility.time.sleep'), \
                mock.patch.object(Utility, 'check_testcase') as check_testcase:
            utility.test_table_count(FakeNode(checksums1, 1), FakeNode(checksums2, 2), 'test')
        return check_testcase.call_args[0][0]

    def test_identical_data_passes(self):
        self.assertEqual(self.run_check({'t1': 111, 't2': 222}, {'t1': 111, 't2': 222}), 0)

    def test_different_checksum_fails(self):
        # The old implementation compared CHECKSUM TABLE's first column (the
        # table name), so this case passed even though the data differed.
        self.assertEqual(self.run_check({'t1': 111, 't2': 222}, {'t1': 111, 't2': 999}), 1)

    def test_table_missing_on_node2_fails(self):
        self.assertEqual(self.run_check({'t1': 111, 't2': 222}, {'t1': 111}), 1)

    def test_table_only_on_node2_fails(self):
        # The old implementation only listed node1's tables, so this passed.
        self.assertEqual(self.run_check({'t1': 111}, {'t1': 111, 't2': 222}), 1)

    def test_checksum_unavailable_on_both_nodes_fails(self):
        # NULL == NULL must not count as matching data.
        self.assertEqual(self.run_check({'t1': None}, {'t1': None}), 1)

    def test_checksum_unavailable_on_one_node_fails(self):
        self.assertEqual(self.run_check({'t1': 111}, {'t1': None}), 1)

    def test_nonpositive_attempts_rejected(self):
        utility = Utility('NO')
        for attempts in (0, -1):
            with self.subTest(attempts=attempts), \
                    mock.patch.object(Utility, 'check_testcase') as check_testcase:
                with self.assertRaises(ValueError):
                    utility.test_table_count(FakeNode({'t1': 1}, 1), FakeNode({'t1': 2}, 2), 'test',
                                             attempts=attempts)
                check_testcase.assert_not_called()

    def test_message_names_the_nodes_compared(self):
        utility = Utility('NO')
        with mock.patch('util.utility.time.sleep'), \
                mock.patch.object(Utility, 'check_testcase'), \
                mock.patch('sys.stdout', new_callable=io.StringIO) as out:
            utility.test_table_count(FakeNode({'t1': 1}, 1), FakeNode({'t1': 1, 't2': 2}, 3), 'test')
        self.assertIn('Table(test.t2) exists only on node3', out.getvalue())

    def test_mismatch_that_resolves_on_recheck_passes(self):
        node1 = FakeNode({'t1': 111}, 1)
        node2 = FakeNode({'t1': 0}, 2)
        calls = []

        def catch_up(_seconds):
            calls.append(_seconds)
            node2.checksums['t1'] = 111

        utility = Utility('NO')
        with mock.patch('util.utility.time.sleep', side_effect=catch_up), \
                mock.patch.object(Utility, 'check_testcase') as check_testcase:
            utility.test_table_count(node1, node2, 'test')
        self.assertEqual(check_testcase.call_args[0][0], 0)
        self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
