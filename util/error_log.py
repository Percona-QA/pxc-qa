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
