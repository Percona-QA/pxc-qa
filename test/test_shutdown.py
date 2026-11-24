"""Unit tests for DbConnection.shutdown() waiting for mysqld to exit.
They need no server: a `sleep` child process stands in for mysqld.

Run from the repository root:
    python3 test/test_shutdown.py
"""
import os
import subprocess
import sys
import tempfile
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

from util import db_connection  # noqa: E402
from util.db_connection import DbConnection, process_running  # noqa: E402


def start_fake_mysqld():
    # Like launch_server(): a direct child of this process.
    return subprocess.Popen(['sleep', '60'], start_new_session=True)


class FakeCursor:
    """Answers SELECT @@pid_file; SHUTDOWN runs `on_shutdown`."""

    def __init__(self, pid_file, on_shutdown):
        self.pid_file = pid_file
        self.on_shutdown = on_shutdown
        self.queries = []

    def execute(self, query):
        self.queries.append(query)
        if query == 'shutdown':
            self.on_shutdown()

    def fetchone(self):
        return (self.pid_file,)


class FakeCnx:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self, buffered=False):
        return self._cursor

    def is_connected(self):
        return False


class TestProcessRunning(unittest.TestCase):

    def test_live_child_is_running(self):
        proc = start_fake_mysqld()
        try:
            self.assertTrue(process_running(proc.pid))
        finally:
            proc.kill()
            proc.wait()

    def test_exited_unreaped_child_is_not_running(self):
        # The zombie case: mysqld exited, nobody called wait() yet.
        proc = subprocess.Popen(['true'])
        deadline = 50
        while deadline and process_running(proc.pid):
            deadline -= 1
            db_connection.time.sleep(0.1)
        self.assertFalse(process_running(proc.pid))


class TestShutdown(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.proc = start_fake_mysqld()
        self.pid_file = os.path.join(self.tmp.name, 'node1.pid')
        with open(self.pid_file, 'w') as handle:
            handle.write(str(self.proc.pid) + '\n')

    def tearDown(self):
        if self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait()
        self.tmp.cleanup()

    def shutdown(self, on_shutdown, timeout):
        node = DbConnection(user='root', socket='/nonexistent', node_num=1, data_dir=self.tmp.name)
        cursor = FakeCursor(self.pid_file, on_shutdown)
        with mock.patch.object(DbConnection, 'connect', return_value=FakeCnx(cursor)), \
                mock.patch.object(DbConnection, '_execute', lambda self, cur, q: cur.execute(q)):
            return node.shutdown(timeout=timeout), cursor

    def test_waits_until_mysqld_exits(self):
        # mysqld takes a moment to exit after SHUTDOWN is accepted.
        delayed_exit = subprocess.Popen(['sh', '-c', 'sleep 2; kill ' + str(self.proc.pid)])
        try:
            start = db_connection.time.monotonic()
            result, cursor = self.shutdown(lambda: None, timeout=30)
            elapsed = db_connection.time.monotonic() - start
        finally:
            delayed_exit.wait()
        self.assertEqual(result, 0)
        self.assertEqual(cursor.queries, ['select @@pid_file', 'shutdown'])
        self.assertGreaterEqual(elapsed, 1.5)
        self.assertFalse(process_running(self.proc.pid))

    def test_hung_mysqld_is_killed_and_reported(self):
        result, _ = self.shutdown(lambda: None, timeout=1)
        self.assertEqual(result, 1)
        self.assertFalse(process_running(self.proc.pid))

    def test_relative_pid_file_is_resolved_against_datadir(self):
        result, _ = self.shutdown(self.proc.terminate, timeout=10)
        self.assertEqual(result, 0)
        self.pid_file = 'node1.pid'
        self.proc = start_fake_mysqld()
        with open(os.path.join(self.tmp.name, 'node1.pid'), 'w') as handle:
            handle.write(str(self.proc.pid))
        result, _ = self.shutdown(self.proc.terminate, timeout=10)
        self.assertEqual(result, 0)
        self.assertFalse(process_running(self.proc.pid))

    def test_pid_lookup_timeout_is_raised_not_reported_as_success(self):
        node = DbConnection(user='root', socket='/nonexistent', node_num=1, data_dir=self.tmp.name)
        cursor = FakeCursor(self.pid_file, lambda: None)

        def hung_execute(_self, cur, query):
            cur.queries.append(query)
            raise db_connection.QueryTimeoutError('select timed out')

        with mock.patch.object(DbConnection, 'connect', return_value=FakeCnx(cursor)), \
                mock.patch.object(DbConnection, '_execute', hung_execute):
            with self.assertRaises(db_connection.QueryTimeoutError):
                node.shutdown(timeout=1)
        self.assertEqual(cursor.queries, ['select @@pid_file'])

    def test_shutdown_error_after_pid_read_still_waits(self):
        # The connection drops while SHUTDOWN is being processed; mysqld exits 2s later.
        delayed_exit = subprocess.Popen(['sh', '-c', 'sleep 2; kill ' + str(self.proc.pid)])

        def dropped():
            raise ConnectionError('Lost connection to MySQL server during query')

        try:
            start = db_connection.time.monotonic()
            result, _ = self.shutdown(dropped, timeout=30)
            elapsed = db_connection.time.monotonic() - start
        finally:
            delayed_exit.wait()
        self.assertEqual(result, 0)
        self.assertGreaterEqual(elapsed, 1.5)
        self.assertFalse(process_running(self.proc.pid))

    def test_shutdown_timeout_kills_known_pid_and_raises(self):
        def hung():
            raise db_connection.QueryTimeoutError('shutdown timed out')

        with self.assertRaises(db_connection.QueryTimeoutError):
            self.shutdown(hung, timeout=30)
        self.assertFalse(process_running(self.proc.pid))

    def test_unreadable_pid_file_falls_back_to_old_behaviour(self):
        self.pid_file = os.path.join(self.tmp.name, 'missing.pid')
        result, cursor = self.shutdown(lambda: None, timeout=1)
        self.assertEqual(result, 0)
        self.assertIn('shutdown', cursor.queries)


if __name__ == '__main__':
    unittest.main()
