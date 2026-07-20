PQA Framework
==============================================================================

PQA Framework is a Python-based test runner for Percona XtraDB Cluster (PXC)
and Percona Server (PS). It runs tests from the `suite/` directory,
and stores logs and failed-test artifacts under the
configured work directory.

Use this project when you want to run one test, selected tests, selected suites,
or suite tests.

Prerequisites
------------------------------------------------------------------------------

Before running the framework, make sure the test host has:

- Python 3.
- `mysql.connector` available to Python.
- A PXC or PS binary tarball extracted on disk.
- `sysbench` installed if running sysbench suites.
- Percona Toolkit configured if running checksum-based tests.
- `pstress` and its grammar file configured if running random QA pstress tests.

The configured MySQL user is usually `root`, and the test servers are started
with local sockets inside the framework work directory.

Configuration
------------------------------------------------------------------------------

The main configuration file is [config.ini](./config.ini). Update it before the
first run so all paths match your local environment.

```ini
[config]
workdir = /dev/shm/qa
basedir = /dev/shm/qa/PXC_tarball
server = pxc
node = 3
user = root
pt_basedir = /dev/shm/qa/percona-toolkit-3.0.10
pstress_bin = /dev/shm/qa/pstress/src/pstress-pxc
pstress_grammar_file = /dev/shm/qa/pstress/src/grammar.sql

[sysbench]
sysbench_user = sysbench
sysbench_pass = sysbench
sysbench_db = sbtest
sysbench_table_count = 10
sysbench_threads = 10
sysbench_normal_table_size = 1000
sysbench_run_time = 300
sysbench_load_test_table_size = 100000
sysbench_random_load_table_size = 1000
sysbench_random_load_run_time = 100
sysbench_oltp_test_table_size = 10000000
sysbench_read_qa_table_size = 100000
sysbench_customized_dataload_table_size = 1000

[upgrade]
pxc_lower_base = /path/to/lower/version/tarball
pxc_upper_base = /path/to/upper/version/tarball
```

Important settings:

- `workdir`: Temporary runtime directory. The framework removes and recreates
  this path at the start of a run.
- `basedir`: Extracted PXC or PS base directory. It must contain `bin/mysqld`.
- `server`: Product to run in tests that support both products. Common values
  are `pxc` and `ps`.
- `node`: Number of nodes to start for cluster/server tests.
- `pt_basedir`: Percona Toolkit base directory.
- `pstress_bin` and `pstress_grammar_file`: Required for pstress tests.
- `pxc_lower_base` and `pxc_upper_base`: Required for upgrade tests.

Custom Server Configuration
------------------------------------------------------------------------------

Default server configuration files are in [conf/](./conf):

- [conf/pxc.cnf](./conf/pxc.cnf) for PXC nodes.
- [conf/ps.cnf](./conf/ps.cnf) for PS nodes.
- [conf/encryption.cnf](./conf/encryption.cnf) for encryption runs.
- [conf/custom.cnf](./conf/custom.cnf) for local custom options.

Add custom MySQL options to `conf/custom.cnf` when you want every generated
server config to include them.

Running Tests
------------------------------------------------------------------------------

Show available runner options:

```bash
python3 qa_framework.py --help
```

Run a single test by filename. The framework searches all known suites:

```bash
python3 qa_framework.py --tests=replication.py
```

Run a single test with an explicit suite name:

```bash
python3 qa_framework.py --tests=replication.replication.py
```

Run multiple tests:

```bash
python3 qa_framework.py --tests=replication.py,gtid_replication.py
```

Run all tests from one suite:

```bash
python3 qa_framework.py --suites=replication
```

Run all tests from multiple suites:

```bash
python3 qa_framework.py --suites=replication,ssl
```

Run with encryption enabled:

```bash
python3 qa_framework.py --tests=ssl.encryption_qa.py --encryption-run
```

Run with debug logging enabled:

```bash
python3 qa_framework.py --tests=replication.py --debug
```

Run suite tests in parallel workers:

```bash
python3 qa_framework.py --suites=replication --number-of-workers=3
```

Available Suites
------------------------------------------------------------------------------

The framework currently recognizes these suite names:

- `sysbench_run`
- `loadtest`
- `replication`
- `correctness`
- `ssl`
- `upgrade`
- `random_qa`
- `galera_sr`

Test and Log Output
------------------------------------------------------------------------------

The framework writes a high-level result file in the repository root, and copies
it to `workdir` once the run completes:

```text
test_run_results.out
<workdir>/test_run_results.out
```

Runtime logs are written under `workdir`:

```text
<workdir>/log/
<workdir>/log/tests_log/
<workdir>/failed_logs/
```

When `--number-of-workers` is used, each worker gets its own directory:

```text
<workdir>/w1/
<workdir>/w2/
<workdir>/w3/
```

Failed tests package logs into `<workdir>/failed_logs/` or the worker-specific
`failed_logs/` directory.

Disabling Tests
------------------------------------------------------------------------------

Tests can be skipped even when explicitly requested via `-t`/`-s` by listing
them in a `disabled.list` file in the script working directory (alongside
`qa_framework.py`):

```text
# Lines starting with '#' are comments and ignored
consistency_check.py
correctness.chaosmonkey-test.py
```

Rules:

- Only entries ending in `.py` are treated as test names; blank lines and
  comments (`#`) are ignored.
- A plain filename (e.g. `consistency_check.py`) skips that test in **every**
  suite it would otherwise run in.
- A suite-qualified name (e.g. `correctness.chaosmonkey-test.py`) skips the test
  **only** within that suite; a same-named test in another suite still runs.
- Skipped tests are reported on stdout and in `test_run_results.out`.
- If `disabled.list` does not exist, no tests are skipped.

Notes:
------------------------------------------------------------------------------

- Run the framework from the repository root so `config.ini` is found.
- Make sure `workdir` is safe to delete before running; it is recreated each run.
- Use explicit suite-qualified test names when two suites may contain tests with
  the same filename.
- If no test is passed and no suite test is found, the runner exits without
  starting any server.
