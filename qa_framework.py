#!/usr/bin/env python3
# Created by Ramesh Sivaraman, Percona LLC.
# QA framework will help us to test Percona XtraDB Cluster and Percona Server.

import os
import argparse
import concurrent.futures
import queue
import shutil
import subprocess
import sys
import threading
from config import *

workdir = WORKDIR

SUITES = ['sysbench_run', 'loadtest', 'replication', 'correctness', 'ssl', 'upgrade',
          'random_qa', 'galera_sr']

EXCLUDED_DEFAULT_SUITES = {'loadtest', 'random_qa', 'upgrade'}
DEFAULT_SUITES = [suite for suite in SUITES if suite not in EXCLUDED_DEFAULT_SUITES]
GLOBAL_MANIFEST_AND_CONFIG_TESTS = ['encryption_qa.py']

# Serializes the stdout+file write pair so concurrent workers can't interleave
# a single message across the console and the results file.
_output_lock = threading.Lock()


def log_output(message, tc_output, flush=True):
    with _output_lock:
        print(message, flush=flush)
        print(message, file=tc_output, flush=flush)


def parse_csv_values(value):
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def validate_suite(scriptdir, suite):
    if suite not in SUITES:
        print('Suite ' + suite + ' is not valid. Valid suites: ' + ', '.join(SUITES))
        exit(1)
    if not os.path.exists(scriptdir + '/suite/' + suite):
        print('Suite ' + suite + '(' + scriptdir + '/suite/' + suite + ') does not exist')
        exit(1)


def get_qualified_test(test):
    for suite in SUITES:
        suite_prefix = suite + '.'
        if test.startswith(suite_prefix):
            test_file_name = test[len(suite_prefix):]
            if test_file_name.endswith('.py'):
                return suite, test_file_name
    return None, os.path.basename(test)


def get_disabled_tests(scriptdir):
    disabled_file = scriptdir + '/disabled.list'
    disabled_qualified = set()
    disabled_any_suite = set()
    if not os.path.isfile(disabled_file):
        return disabled_qualified, disabled_any_suite
    with open(disabled_file, 'r') as handle:
        for line in handle:
            entry = line.strip()
            if not entry or entry.startswith('#'):
                continue
            if not entry.endswith('.py'):
                continue
            test_suite, test_file_name = get_qualified_test(entry)
            if test_suite:
                disabled_qualified.add((test_suite, test_file_name))
            else:
                disabled_any_suite.add(test_file_name)
    return disabled_qualified, disabled_any_suite


def filter_disabled_tests(test_runs, disabled_tests, tc_output):
    disabled_qualified, disabled_any_suite = disabled_tests
    if not disabled_qualified and not disabled_any_suite:
        return test_runs
    filtered_test_runs = []
    for test_run in test_runs:
        test_name = os.path.basename(test_run[0])
        suite_name = test_run[1]
        if test_name in disabled_any_suite or (suite_name, test_name) in disabled_qualified:
            message = 'Skipping disabled test ' + suite_name + '.' + test_name
            log_output(message, tc_output)
            continue
        filtered_test_runs.append(test_run)
    log_output("", tc_output)
    return filtered_test_runs


def is_global_manifest_and_config_test(test_run):
    return os.path.basename(test_run[0]) in GLOBAL_MANIFEST_AND_CONFIG_TESTS


def filter_global_manifest_and_config_tests(test_runs, tc_output):
    global_manifest_and_config_runs = [test_run for test_run in test_runs if is_global_manifest_and_config_test(test_run)]
    if not global_manifest_and_config_runs or len(test_runs) == len(global_manifest_and_config_runs):
        return test_runs
    filtered_test_runs = []
    for test_run in test_runs:
        if is_global_manifest_and_config_test(test_run):
            suite_name = test_run[1]
            test_name = os.path.basename(test_run[0])
            message = ('Skipping ' + suite_name + '.' + test_name +
                       ' - cannot run together with other tests in encryption mode '
                       'as it changes the global keyring file')
            log_output(message, tc_output)
            continue
        filtered_test_runs.append(test_run)
    log_output("", tc_output)
    return filtered_test_runs


def find_test_runs(scriptdir, tests, suites, tc_output):
    test_runs = []
    search_suites = suites
    if len(search_suites) == 0:
        search_suites = SUITES
    log_output("#" * 80, tc_output)
    for test in tests:
        test_suite, test_file_name = get_qualified_test(test)
        if test_suite:
            validate_suite(scriptdir, test_suite)
            test_file = scriptdir + '/suite/' + test_suite + '/' + test_file_name
            if not os.path.isfile(test_file):
                print(test + ' does not exist')
                exit(1)
            log_output("Adding test " + test_file, tc_output)
            test_runs.append((test_file, test_suite))
            continue

        test_found = False
        for suite in search_suites:
            test_file = scriptdir + '/suite/' + suite + '/' + test_file_name
            if os.path.isfile(test_file):
                log_output("Adding test " + test_file, tc_output)
                test_runs.append((test_file, suite))
                test_found = True
        if not test_found:
            print(test_file_name + ' does not exist in specified suites')
            exit(1)
    log_output("", tc_output)
    return test_runs


def add_suite_test_runs(scriptdir, suites, tc_output, debug):
    test_runs = []
    log_output("#" * 80, tc_output)
    for suite in suites:
        log_output("Adding tests from " + suite + " suite", tc_output)
        for file in os.listdir(scriptdir + '/suite/' + suite):
            if file.endswith(".py"):
                if debug:
                    log_output("Adding test " + scriptdir + '/suite/' + suite + '/' + file, tc_output)
                test_runs.append((scriptdir + '/suite/' + suite + '/' + file, suite))
        log_output("", tc_output)
    return test_runs

def make_workdir(number_of_workers=0):
    if os.path.exists(workdir):
        print('Work directory ' + workdir + ' already exists, removing it')
        shutil.rmtree(workdir, ignore_errors=True)
    print('Creating work directory ' + workdir)
    os.makedirs(workdir)
    if number_of_workers > 0:
        for worker_id in range(1, number_of_workers + 1):
            worker_dir = get_worker_thread_dir(worker_id)
            os.makedirs(worker_dir)
            os.makedirs(worker_dir + '/log')
            os.makedirs(worker_dir + '/conf')
            os.makedirs(worker_dir + '/failed_logs')
            os.makedirs(worker_dir + '/log' + '/tests_log')
    else:
        os.makedirs(workdir + '/log')
        os.makedirs(workdir + '/conf')
        os.makedirs(workdir + '/failed_logs')
        os.makedirs(workdir + '/log' + '/tests_log')

def get_worker_thread_dir(worker_id=0):
    if worker_id > 0:
        return workdir + '/w' + str(worker_id)
    return workdir


def run_test(test_file, suite_name, encryption, tc_output, debug, worker_id=0):
    cmd = test_file
    if encryption:
        cmd = cmd + ' -e'
    if debug:
        cmd = cmd + ' -d'
    worker_option = ''
    if worker_id > 0:
        worker_option = '-' + str(worker_id)
    if worker_option:
        cmd = cmd + ' ' + worker_option
    if debug:
        log_output("Running test : " + cmd, tc_output)
    result = subprocess.call(cmd, shell=True)
    return worker_id, suite_name, os.path.basename(test_file), result


def run_worker_tests(worker_id, test_queue, encryption, debug, tc_output, output_lock):
    worker_failed = False
    while True:
        try:
            test_run = test_queue.get_nowait()
        except queue.Empty:
            break
        try:
            result = run_test(test_run[0], test_run[1], encryption, tc_output, debug, worker_id)
            with output_lock:
                worker_failed = handle_test_result(tc_output, *result) or worker_failed
        finally:
            test_queue.task_done()
    return worker_failed


def handle_test_result(tc_output, worker_id, suite_name, file, result):
    worker = ''
    if worker_id > 0:
        worker = 'w' + str(worker_id) + ' '
    test_name = f'{suite_name}.{file}'
    if result == 0:
        output = 'Test ' + f'{test_name:60}' + worker + '[Pass]'
    else:
        output = 'Test ' + f'{test_name:60}' + worker + '[Fail]'
    log_output(output, tc_output)
    if result != 0:
        workdir = get_worker_thread_dir(worker_id)
        print_failed_test_log(tc_output, workdir, file)
        os.system('tar -czf ' + workdir + '/failed_logs/' + suite_name + '_' +
                  file + '.tar.gz ' + workdir + '/log/*')
    return result != 0


def print_failed_test_log(tc_output, workdir, file, num_lines=10):
    test_log_file = workdir + '/log' + '/tests_log/' + os.path.splitext(file)[0] + '.log'
    header = 'Test results at the time of failure:'
    if not os.path.isfile(test_log_file):
        message = 'Failed test log file not found: ' + test_log_file
        log_output(message, tc_output)
        return
    from collections import deque
    with open(test_log_file, 'r', errors='replace') as log_file:
        last_lines = list(deque(log_file, maxlen=num_lines))
    log_output(header, tc_output)
    for line in last_lines:
        log_output(line.rstrip('\n'), tc_output)
    log_output("Check the log file for more details: " + test_log_file, tc_output)


def main():
    """ This function will help us to run PS/PXC QA scripts.
        We can initiate complete test suite or individual
        testcase using this function.
    """
    tc_output_file = 'test_run_results.out'
    tc_output = open(tc_output_file, 'w')
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(prog='QA Framework', usage='%(prog)s [options]')
    parser.add_argument('-t', '--tests', '--test', default='', dest='tests',
                        help='Specify comma-separated test file names or suite.test_file.py names')
    parser.add_argument('-s', '-S', '--suites', '--suite', default='', dest='suites',
                        help='Specify comma-separated suite names (default: all suites except '
                             + ', '.join(sorted(EXCLUDED_DEFAULT_SUITES)) + ' when -t is not used)')
    parser.add_argument('-e', '--encryption-run', action='store_true',
                        help='This option will enable encryption options')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='This option will enable debug logging')
    parser.add_argument('-w', '--number-of-workers', type=int, default=0,
                        help='Specify number of workers to run the test suite in parallel')
    args = parser.parse_args()
    encryption = args.encryption_run
    debug = args.debug
    tests = parse_csv_values(args.tests)
    suites = parse_csv_values(args.suites)
    number_of_workers = args.number_of_workers
    test_runs = []
    for suite in suites:
        validate_suite(scriptdir, suite)

    if len(tests) == 0:
        if len(suites) == 0:
            suites = DEFAULT_SUITES
            log_output('Running default suites: ' + ', '.join(suites), tc_output)
        test_runs.extend(add_suite_test_runs(scriptdir, suites, tc_output, debug))
    else:
        test_runs.extend(find_test_runs(scriptdir, tests, suites, tc_output))

    test_runs = filter_disabled_tests(test_runs, get_disabled_tests(scriptdir), tc_output)
    if encryption:
        test_runs = filter_global_manifest_and_config_tests(test_runs, tc_output)

    if len(test_runs) != 0:
        make_workdir(number_of_workers)
    else:
        print('Either no test passed to run or no test found in specified suites to run')
        tc_output.close()
        sys.exit(1)

    log_output("#" * 80 + "\n", tc_output)

    any_failed = False
    if number_of_workers > 0:
        test_queue = queue.Queue()
        for test_run in test_runs:
            test_queue.put(test_run)
        output_lock = threading.Lock()
        with concurrent.futures.ThreadPoolExecutor(max_workers=number_of_workers) as executor:
            futures = [executor.submit(run_worker_tests, worker_id, test_queue, encryption, debug,
                                       tc_output, output_lock)
                       for worker_id in range(1, number_of_workers + 1)]
            for future in concurrent.futures.as_completed(futures):
                any_failed = future.result() or any_failed
    else:
        for test_run in test_runs:
            any_failed = handle_test_result(tc_output, *run_test(test_run[0], test_run[1],
                                                                 encryption, tc_output, debug))

    tc_output.close()
    if os.path.isdir(workdir):
        shutil.copy(tc_output_file, workdir)
    if any_failed:
        print('Some of the tests failed in the test run, please check the log file for more details')
        sys.exit(1)
    else:
        print('All tests passed in the test run')
        sys.exit(0)

if __name__ == "__main__":
    main()
