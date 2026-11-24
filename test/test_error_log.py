"""Unit tests for util/error_log.py and the test runner's crash check.
They need no server.

Run from the repository root (config.py reads ./config.ini):
    python3 test/test_error_log.py
"""
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../'))
sys.path.insert(0, parent_dir)

from util import error_log  # noqa: E402
import qa_framework  # noqa: E402

# Lines taken from real PXC 8.4 error logs.
CRASH_LINES = [
    '2026-11-03T21:17:24Z UTC - mysqld got signal 6 ;',
    '2026-11-03T21:17:24.650040Z 1 [ERROR] [MY-013183] [InnoDB] Assertion failure: '
    'lock0lock.cc:336:lock_latest_err_file thread 127909209216704',
    "mysqld: /src/sql/handler.cc:123: int foo(): Assertion `thd != nullptr' failed.",
    '==12345==ERROR: AddressSanitizer: heap-use-after-free on address 0x6020',
    '==12345==ERROR: LeakSanitizer: detected memory leaks',
    'WARNING: ThreadSanitizer: data race (pid=12345)',
    '==12345==WARNING: MemorySanitizer: use-of-uninitialized-value',
    '/src/storage/innobase/row/row0mysql.cc:42:7: runtime error: signed integer overflow',
    "terminate called after throwing an instance of 'std::bad_alloc'",
    '2026-11-23T20:51:15Z 0 [ERROR] [MY-012153] [InnoDB] Database page corruption on disk or a failed file read',
    '2026-11-23T20:51:15Z 0 [ERROR] [MY-000000] [Galera] Inconsistency detected: Inconsistent by consensus',
]

CLEAN_LINES = [
    '2026-11-23T20:51:15.731456Z 0 [ERROR] [MY-000000] [WSREP-SST] socat not found in path',
    '2026-11-23T20:51:15Z 0 [ERROR] [MY-000067] [Server] unknown variable \'foo=1\'.',
    '2026-11-23T20:51:15Z 0 [ERROR] [MY-010119] [Server] Aborting',
    # Boilerplate printed after any crash; the crash line itself is what counts.
    'InnoDB: corruption in the InnoDB tablespace. Please refer to',
    '2026-11-23T20:51:09Z 0 [Note] [MY-012550] [InnoDB] Database was not shutdown normally!',
    '2026-11-23T20:51:15Z 0 [Note] [MY-000000] [Galera] Received SELF-LEAVE. Closing connection.',
    # Informational sanitizer output, not a report.
    '==12345==INFO: AddressSanitizer ignores mlock/mlockall/munlock/munlockall',
    '==12345==WARNING: AddressSanitizer failed to allocate 0x10000000000 bytes',
]


class TestScanErrorLog(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log_dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, lines):
        path = os.path.join(self.log_dir, name)
        with open(path, 'w') as handle:
            handle.write('\n'.join(lines) + '\n')
        return path

    def test_each_crash_line_is_found(self):
        for line in CRASH_LINES:
            with self.subTest(line=line):
                path = self.write('node1.err', CLEAN_LINES + [line])
                findings = error_log.scan_error_log(path)
                self.assertEqual([f[2] for f in findings], [line])
                self.assertEqual(findings[0][0], len(CLEAN_LINES) + 1)

    def test_clean_log_has_no_findings(self):
        path = self.write('node1.err', CLEAN_LINES)
        self.assertEqual(error_log.scan_error_log(path), [])

    def test_allowed_pattern_suppresses_finding(self):
        import re
        path = self.write('node1.err', [CRASH_LINES[0]])
        self.assertEqual(error_log.scan_error_log(path, [re.compile('got signal 6')]), [])

    def test_scan_covers_node_ps_and_init_logs_only(self):
        self.write('node2.err', [CRASH_LINES[0]])
        self.write('psnode1.err', [CRASH_LINES[1]])
        self.write('init3.log', [CRASH_LINES[2]])
        self.write('ps_init1.log', [CRASH_LINES[3]])
        self.write('node1.err', CLEAN_LINES)
        self.write('sysbench.log', [CRASH_LINES[0]])
        results = error_log.scan_error_logs(self.log_dir)
        self.assertEqual(sorted(os.path.basename(p) for p in results),
                         ['init3.log', 'node2.err', 'ps_init1.log', 'psnode1.err'])

    def test_clear_removes_only_error_logs(self):
        self.write('node1.err', CLEAN_LINES)
        self.write('init1.log', CLEAN_LINES)
        self.write('ps_init1.log', CLEAN_LINES)
        self.write('sysbench.log', CLEAN_LINES)
        error_log.clear_error_logs(self.log_dir)
        self.assertEqual(os.listdir(self.log_dir), ['sysbench.log'])

    def test_format_caps_findings_per_file(self):
        path = self.write('node1.err', [CRASH_LINES[0]] * 15)
        lines = error_log.format_findings(error_log.scan_error_logs(self.log_dir))
        self.assertEqual(lines[0], 'Crash markers in ' + path + ':')
        self.assertEqual(len(lines), 1 + error_log.MAX_FINDINGS_PER_FILE + 1)
        self.assertEqual(lines[-1], '  ... 5 more')


class TestWaitForServers(unittest.TestCase):

    PGREP = ('101 /pxc/bin/mysqld --defaults-file=/qa/conf/node1.cnf --datadir=/qa/node1\n'
             '102 /pxc/bin/mysqld --defaults-file=/qa/w1/conf/node1.cnf --datadir=/qa/w1/node1\n'
             '103 /pxc/bin/mysqld --defaults-file=/qa//conf/ps1.cnf --datadir=/qa//psnode1\n'
             '104 /usr/sbin/mysqld --defaults-file=/etc/mysql/my.cnf\n'
             '105 /pxc/bin/mysqld --defaults-file=/qa/conf/sub/x.cnf\n'
             '106 /pxc/bin/mysqld --no-defaults --datadir=/qa/conf/\n')

    def test_only_this_workers_servers_are_matched(self):
        with mock.patch.object(error_log.subprocess, 'run',
                               return_value=mock.Mock(stdout=self.PGREP)):
            self.assertEqual(error_log.worker_server_pids('/qa'), [101, 103])
            self.assertEqual(error_log.worker_server_pids('/qa/'), [101, 103])
            self.assertEqual(error_log.worker_server_pids('/qa/w1/'), [102])

    def test_waits_for_servers_that_exit(self):
        running = [[101], [101], []]
        with mock.patch.object(error_log, 'worker_server_pids', side_effect=lambda d: running.pop(0)), \
                mock.patch.object(error_log.time, 'sleep'), \
                mock.patch.object(error_log.os, 'kill') as kill:
            self.assertEqual(error_log.wait_for_servers_to_exit('/qa', timeout=60), ([], []))
        kill.assert_not_called()

    def test_kills_servers_still_running_after_timeout(self):
        with mock.patch.object(error_log, 'worker_server_pids', side_effect=[[101], [], []]), \
                mock.patch.object(error_log.time, 'sleep'), \
                mock.patch.object(error_log.os, 'kill') as kill:
            self.assertEqual(error_log.wait_for_servers_to_exit('/qa', timeout=0), ([101], []))
        kill.assert_called_once_with(101, error_log.signal.SIGKILL)

    def test_reports_servers_that_survive_sigkill(self):
        clock = iter(range(0, 1000, 10))
        with mock.patch.object(error_log, 'worker_server_pids', return_value=[101]), \
                mock.patch.object(error_log.time, 'sleep'), \
                mock.patch.object(error_log.time, 'monotonic', side_effect=lambda: next(clock)), \
                mock.patch.object(error_log.os, 'kill'):
            self.assertEqual(error_log.wait_for_servers_to_exit('/qa', timeout=0), ([101], [101]))


class TestHandleTestResult(unittest.TestCase):

    def handle(self, result, crash_findings, killed_pids=None, surviving_pids=None):
        with mock.patch.object(qa_framework, 'print_failed_test_log'), \
                mock.patch.object(qa_framework.os, 'system'), \
                mock.patch('sys.stdout', new_callable=io.StringIO) as out:
            failed = qa_framework.handle_test_result(io.StringIO(), 0, 'correctness', 'x.py', result,
                                                     1, crash_findings, killed_pids, surviving_pids)
        return failed, out.getvalue()

    def test_passing_test_with_crash_fails(self):
        failed, out = self.handle(0, {'/w/log/node2.err': [(7, 'mysqld crashed on a signal', CRASH_LINES[0])]})
        self.assertTrue(failed)
        self.assertIn('[Fail]', out)
        self.assertIn('line 7 (mysqld crashed on a signal)', out)

    def test_skipped_test_with_crash_fails(self):
        failed, _ = self.handle(qa_framework.SKIP_TEST_EXIT_CODE,
                                {'/w/log/node1.err': [(1, 'assertion failure', CRASH_LINES[1])]})
        self.assertTrue(failed)

    def test_killed_servers_are_reported(self):
        failed, out = self.handle(0, {}, killed_pids=[101])
        self.assertFalse(failed)
        self.assertIn('Killed mysqld process(es) still running', out)

    def test_server_surviving_sigkill_fails_test(self):
        failed, out = self.handle(0, {}, killed_pids=[101], surviving_pids=[101])
        self.assertTrue(failed)
        self.assertIn('still running 30s after SIGKILL: 101', out)

    def test_passing_test_without_crash_passes(self):
        failed, out = self.handle(0, {})
        self.assertFalse(failed)
        self.assertIn('[Pass]', out)


if __name__ == '__main__':
    unittest.main()
