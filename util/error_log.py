"""Scan mysqld error logs for crashes, assertions, sanitizer reports,
corruption and Galera inconsistency.

A test can pass while one of its nodes crashed and was restarted, so the
test runner scans every node's error log after each test and fails the
test when one of these markers shows up.

Only high-signal markers are matched. Plain "[ERROR]" lines are not:
tests routinely provoke expected errors (bad options, refused SST, etc.).
"""
import glob
import os
import re
import signal
import subprocess
import time

# (description, pattern) pairs. Each pattern is matched against one log line.
CRASH_PATTERNS = [
    ('mysqld crashed on a signal', re.compile(r'mysqld got signal \d+')),
    ('assertion failure', re.compile(r'Assertion failure:|Assertion `.*\' failed')),
    # Sanitizer reports start with "ERROR: <Name>Sanitizer: " or "WARNING: <Name>Sanitizer: ";
    # informational lines such as "INFO: AddressSanitizer ignores mlock/..." do not.
    ('sanitizer report', re.compile(r'(ERROR|WARNING): (Address|Thread|Memory|Leak)Sanitizer: |runtime error: ')),
    ('uncaught C++ exception', re.compile(r'terminate called after throwing')),
    ('InnoDB corruption', re.compile(r'\[ERROR\].*\[InnoDB\].*[Cc]orrupt|Database page corruption')),
    ('Galera inconsistency', re.compile(r'Inconsistency detected|Node consistency compromised')),
]

# Lines matching any of these are ignored even if they match CRASH_PATTERNS.
# Add a pattern here (with a comment saying why) when a test is expected to
# produce one of the markers above.
ALLOWED_PATTERNS = []

# Files in a worker's log directory that mysqld writes to.
ERROR_LOG_GLOBS = ['*.err', 'init*.log', 'ps_init*.log']

MAX_FINDINGS_PER_FILE = 10

# How long the runner waits for a finished test's mysqld processes to exit
# before scanning their logs.
SERVER_EXIT_TIMEOUT = 120


def scan_error_log(path, allowed_patterns=None):
    """Return [(line_number, description, line)] for crash markers in `path`."""
    if allowed_patterns is None:
        allowed_patterns = ALLOWED_PATTERNS
    findings = []
    with open(path, 'r', errors='replace') as log_file:
        for line_number, line in enumerate(log_file, 1):
            for description, pattern in CRASH_PATTERNS:
                if pattern.search(line):
                    if not any(allowed.search(line) for allowed in allowed_patterns):
                        findings.append((line_number, description, line.rstrip('\n')))
                    break
    return findings


def error_log_files(log_dir):
    files = set()
    for pattern in ERROR_LOG_GLOBS:
        files.update(glob.glob(os.path.join(log_dir, pattern)))
    return sorted(files)


def scan_error_logs(log_dir, allowed_patterns=None):
    """Return {path: findings} for every error log in `log_dir` with findings."""
    results = {}
    for path in error_log_files(log_dir):
        findings = scan_error_log(path, allowed_patterns)
        if findings:
            results[path] = findings
    return results


def format_findings(results):
    """Turn scan_error_logs() output into report lines."""
    lines = []
    for path, findings in results.items():
        lines.append('Crash markers in ' + path + ':')
        for line_number, description, line in findings[:MAX_FINDINGS_PER_FILE]:
            lines.append('  line ' + str(line_number) + ' (' + description + '): ' + line.strip())
        if len(findings) > MAX_FINDINGS_PER_FILE:
            lines.append('  ... ' + str(len(findings) - MAX_FINDINGS_PER_FILE) + ' more')
    return lines


def clear_error_logs(log_dir):
    """Remove error logs left by the previous test in this log directory."""
    for path in error_log_files(log_dir):
        os.remove(path)


def worker_server_pids(worker_dir):
    """Pids of mysqld processes started with a config file from this worker's conf/ directory.
    Paths are normalized, since some callers build them with doubled slashes."""
    conf_dir = os.path.normpath(os.path.join(worker_dir, 'conf'))
    try:
        output = subprocess.run(['pgrep', '-a', 'mysqld'], capture_output=True, text=True).stdout
    except FileNotFoundError:
        return []
    pids = []
    for line in output.splitlines():
        fields = line.split()
        for arg in fields[1:]:
            if arg.startswith('--defaults-file='):
                conf_file = os.path.normpath(arg[len('--defaults-file='):])
                if os.path.dirname(conf_file) == conf_dir:
                    pids.append(int(fields[0]))
                break
    return pids


def wait_for_servers_to_exit(worker_dir, timeout=SERVER_EXIT_TIMEOUT, poll_interval=1):
    """Wait until no mysqld from this worker is running, so their error logs are
    complete before they are scanned: a crash during shutdown is written after
    SHUTDOWN returns. Servers still running after `timeout` seconds are killed
    with SIGKILL so they can't leak into the next test.
    Returns (killed, surviving): the pids that had to be killed, and those
    still running 30s after SIGKILL (e.g. stuck in uninterruptible I/O).
    """
    deadline = time.monotonic() + timeout
    pids = worker_server_pids(worker_dir)
    while pids and time.monotonic() < deadline:
        time.sleep(poll_interval)
        pids = worker_server_pids(worker_dir)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if not pids:
        return [], []
    surviving = [pid for pid in worker_server_pids(worker_dir) if pid in pids]
    kill_deadline = time.monotonic() + 30
    while surviving and time.monotonic() < kill_deadline:
        time.sleep(poll_interval)
        surviving = [pid for pid in worker_server_pids(worker_dir) if pid in pids]
    return pids, surviving
