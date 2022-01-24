Sysbench Loadtest QA script
---------------------------
This suite will help us to test the workload in Percona XtraDB Cluster. To enable encryption options you should use the argument --encryption-run with pxc qa framework.

Currently we are using following sysbench testsuite for workload test.
* sysbench_customized_dataload_test.py
  * This testsuite will help us to test PXC with different table creation options
* sysbench_load_test.py
  * This testsuite will help us to test PXC with huge tables. 
* sysbench_oltp_test.py
  * This testsuite will help us to test PXC with OLTP transactions.
* sysbench_random_load_test.py
  * This testsuite will help us to test PXC with random load.
* sysbench_read_only_test.py
  * This testsuite will help us to test PXC with read only transactions.
* sysbench_wsrep_provider_option_random_test.py
  * This testsuite will help us to test PXC with different wsrep provider options

PS : We can customize the sysbench data size through [config.ini](../config.ini)

Sysbench Loadtest suite log
---------------------
```
python3 qa_framework.py --testname=suite/loadtest/sysbench_wsrep_provider_option_random_test.py

--------------------------------

PXC WSREP provider random test
--------------------------------
16:40:18  Startup sanity check                                                                                [ ✓ ]
16:40:25  Initializing cluster                                                                                [ ✓ ]
16:40:25  Configuration file creation                                                                         [ ✓ ]
16:41:15  Cluster startup                                                                                     [ ✓ ]
16:41:15  Database connection                                                                                 [ ✓ ]
16:41:15  Sysbench run sanity check                                                                           [ ✓ ]
16:41:18  Sysbench data load                                                                                  [ ✓ ]
16:41:32  PXC: shutting down cluster node3                                                                    [ ✓ ]
16:41:46  PXC: shutting down cluster node2                                                                    [ ✓ ]
16:41:47  PXC: shutting down cluster node1                                                                    [ ✓ ]


python3 qa_framework.py --testname=suite/loadtest/sysbench_load_test.py

-------------------------

PXC sysbench load test
------------------------
16:57:11  Startup sanity check                                                                                [ ✓ ]
16:57:11  Configuration file creation                                                                         [ ✓ ]
16:57:17  Initializing cluster                                                                                [ ✓ ]
16:58:04  Cluster startup                                                                                     [ ✓ ]
16:58:04  Database connection                                                                                 [ ✓ ]
16:58:04  Sysbench run sanity check                                                                           [ ✓ ]
16:58:04  Sysbench data cleanup (threads : 32)                                                                [ ✓ ]
16:58:05  Sysbench data load (threads : 32)                                                                   [ ✓ ]
16:58:10  Checksum run for DB: test                                                                           [ ✓ ]
16:58:10  Sysbench data cleanup (threads : 64)                                                                [ ✓ ]
16:58:10  Sysbench data load (threads : 64)                                                                   [ ✓ ]
16:58:16  Checksum run for DB: test                                                                           [ ✓ ]
16:58:16  Sysbench data cleanup (threads : 128)                                                               [ ✓ ]
16:58:17  Sysbench data load (threads : 128)                                                                  [ ✓ ]
16:58:22  Checksum run for DB: test                                                                           [ ✓ ]
16:58:23  Sysbench data cleanup (threads : 256)                                                               [ ✓ ]
16:58:25  Sysbench data load (threads : 256)                                                                  [ ✓ ]
16:58:30  Checksum run for DB: test                                                                           [ ✓ ]
16:58:32  Sysbench data cleanup (threads : 1024)                                                              [ ✓ ]
16:58:49  Sysbench data load (threads : 1024)                                                                 [ ✓ ]
16:58:54  Checksum run for DB: test                                                                           [ ✓ ]
16:59:08  PXC: shutting down cluster node3                                                                    [ ✓ ]
16:59:23  PXC: shutting down cluster node2                                                                    [ ✓ ]
16:59:37  PXC: shutting down cluster node1                                                                    [ ✓ ]


python3 qa_framework.py --testname=suite/loadtest/sysbench_random_load_test.py

-------------------------------

PXC sysbench random load test
-------------------------------
16:59:46  Startup sanity check                                                                                [ ✓ ]
16:59:46  Configuration file creation                                                                         [ ✓ ]
16:59:52  Initializing cluster                                                                                [ ✓ ]
17:00:44  Cluster startup                                                                                     [ ✓ ]
17:00:44  Database connection                                                                                 [ ✓ ]
17:00:44  Sysbench run sanity check                                                                           [ ✓ ]
17:00:44  Sysbench data cleanup (threads : 50)                                                                [ ✓ ]
17:00:44  Sysbench data load (threads : 50)                                                                   [ ✓ ]


python3 qa_framework.py --testname=suite/sysbench_run/sysbench_customized_dataload_test.py

----------------------------------------

PXC sysbench customized data load test
----------------------------------------
10:33:39  Startup sanity check                                                                                [ ✓ ]
10:33:39  Configuration file creation                                                                         [ ✓ ]
10:33:44  Initializing cluster                                                                                [ ✓ ]
10:34:35  Cluster startup                                                                                     [ ✓ ]
10:34:35  Database connection                                                                                 [ ✓ ]
10:34:35  Sysbench run sanity check                                                                           [ ✓ ]
10:34:54  Sysbench data load                                                                                  [ ✓ ]
10:35:08  PXC: shutting down cluster node3                                                                    [ ✓ ]
10:35:23  PXC: shutting down cluster node2                                                                    [ ✓ ]
10:35:37  PXC: shutting down cluster node1                                                                    [ ✓ ]


python3 qa_framework.py --testname=suite/sysbench_run/sysbench_oltp_test.py

------------------------

PXC sysbench oltp test
------------------------
10:35:47  Startup sanity check                                                                                [ ✓ ]
10:35:47  Configuration file creation                                                                         [ ✓ ]
10:35:53  Initializing cluster                                                                                [ ✓ ]
10:36:44  Cluster startup                                                                                     [ ✓ ]
10:36:44  Database connection                                                                                 [ ✓ ]
10:36:44  Sysbench run sanity check                                                                           [ ✓ ]
10:36:45  Sysbench data load                                                                                  [ ✓ ]
10:36:57  Sysbench oltp(rand_type:uniform, delete_inserts:10,idx_updates:10, non_idx_updates:10) run          [ ✓ ]
10:37:32  Sysbench oltp(rand_type:uniform, delete_inserts:10,idx_updates:10, non_idx_updates:20) run          [ ✓ ]
10:37:59  Sysbench oltp(rand_type:uniform, delete_inserts:10,idx_updates:10, non_idx_updates:30) run          [ ✓ ]
10:38:15  Sysbench oltp(rand_type:uniform, delete_inserts:10,idx_updates:10, non_idx_updates:40) run          [ ✓ ]
10:38:43  Sysbench oltp(rand_type:uniform, delete_inserts:10,idx_updates:10, non_idx_updates:50) run          [ ✓ ]
10:38:57  Sysbench oltp(rand_type:uniform, delete_inserts:10,idx_updates:20, non_idx_updates:10) run          [ ✓ ]
10:39:11  Sysbench oltp(rand_type:uniform, delete_inserts:10,idx_updates:20, non_idx_updates:20) run          [ ✓ ]
10:41:12  Checksum run for DB: test                                                                           [ ✓ ]


python3 qa_framework.py --testname=suite/sysbench_run/sysbench_read_only_test.py

-----------------------------

PXC sysbench read only test
-----------------------------
10:47:08  Startup sanity check                                                                                [ ✓ ]
10:47:08  Configuration file creation                                                                         [ ✓ ]
10:47:14  Initializing cluster                                                                                [ ✓ ]
10:48:05  Cluster startup                                                                                     [ ✓ ]
10:48:05  Database connection                                                                                 [ ✓ ]
10:48:05  Sysbench run sanity check                                                                           [ ✓ ]
10:48:07  Sysbench data load                                                                                  [ ✓ ]
10:48:17  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:1, point_selects:10, order_rng:2) run      [ ✓ ]
10:48:28  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:1, point_selects:20, order_rng:2) run      [ ✓ ]
10:48:38  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:1, point_selects:30, order_rng:2) run      [ ✓ ]
10:48:48  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:1, point_selects:10, order_rng:5) run      [ ✓ ]
10:48:58  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:1, point_selects:20, order_rng:5) run      [ ✓ ]
10:49:08  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:1, point_selects:30, order_rng:5) run      [ ✓ ]
10:49:18  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:1, point_selects:10, order_rng:8) run      [ ✓ ]
10:49:28  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:1, point_selects:20, order_rng:8) run      [ ✓ ]
10:49:38  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:1, point_selects:30, order_rng:8) run      [ ✓ ]
10:49:48  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:3, point_selects:10, order_rng:2) run      [ ✓ ]
10:49:58  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:3, point_selects:20, order_rng:2) run      [ ✓ ]
10:50:08  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:3, point_selects:30, order_rng:2) run      [ ✓ ]
10:50:19  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:3, point_selects:10, order_rng:5) run      [ ✓ ]
10:50:30  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:3, point_selects:20, order_rng:5) run      [ ✓ ]
10:50:40  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:3, point_selects:30, order_rng:5) run      [ ✓ ]
10:50:50  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:3, point_selects:10, order_rng:8) run      [ ✓ ]
10:51:00  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:3, point_selects:20, order_rng:8) run      [ ✓ ]
10:51:10  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:3, point_selects:30, order_rng:8) run      [ ✓ ]
10:51:20  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:5, point_selects:10, order_rng:2) run      [ ✓ ]
10:51:30  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:5, point_selects:20, order_rng:2) run      [ ✓ ]
10:51:40  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:5, point_selects:30, order_rng:2) run      [ ✓ ]
10:51:51  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:5, point_selects:10, order_rng:5) run      [ ✓ ]
10:52:02  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:5, point_selects:20, order_rng:5) run      [ ✓ ]
10:52:22  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:5, point_selects:30, order_rng:5) run      [ ✓ ]
10:52:33  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:5, point_selects:10, order_rng:8) run      [ ✓ ]
10:52:43  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:5, point_selects:20, order_rng:8) run      [ ✓ ]
10:53:13  Sysbench read only(distinct_rng:3, sum_rng:2, simple_rng:5, point_selects:30, order_rng:8) run      [ ✓ ]
10:53:23  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:1, point_selects:10, order_rng:2) run      [ ✓ ]
10:53:33  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:1, point_selects:20, order_rng:2) run      [ ✓ ]
10:53:56  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:1, point_selects:30, order_rng:2) run      [ ✓ ]
10:54:06  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:1, point_selects:10, order_rng:5) run      [ ✓ ]
10:54:16  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:1, point_selects:20, order_rng:5) run      [ ✓ ]
10:54:26  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:1, point_selects:30, order_rng:5) run      [ ✓ ]
10:54:36  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:1, point_selects:10, order_rng:8) run      [ ✓ ]
10:54:46  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:1, point_selects:20, order_rng:8) run      [ ✓ ]
10:54:56  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:1, point_selects:30, order_rng:8) run      [ ✓ ]
10:55:06  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:3, point_selects:10, order_rng:2) run      [ ✓ ]
10:55:17  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:3, point_selects:20, order_rng:2) run      [ ✓ ]
10:55:27  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:3, point_selects:30, order_rng:2) run      [ ✓ ]
10:55:37  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:3, point_selects:10, order_rng:5) run      [ ✓ ]
10:55:47  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:3, point_selects:20, order_rng:5) run      [ ✓ ]
10:55:57  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:3, point_selects:30, order_rng:5) run      [ ✓ ]
10:56:07  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:3, point_selects:10, order_rng:8) run      [ ✓ ]
10:56:17  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:3, point_selects:20, order_rng:8) run      [ ✓ ]
10:56:27  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:3, point_selects:30, order_rng:8) run      [ ✓ ]
10:56:38  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:5, point_selects:10, order_rng:2) run      [ ✓ ]
10:56:48  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:5, point_selects:20, order_rng:2) run      [ ✓ ]
10:56:58  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:5, point_selects:30, order_rng:2) run      [ ✓ ]
10:57:08  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:5, point_selects:10, order_rng:5) run      [ ✓ ]
10:57:18  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:5, point_selects:20, order_rng:5) run      [ ✓ ]
10:57:28  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:5, point_selects:30, order_rng:5) run      [ ✓ ]
10:57:39  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:5, point_selects:10, order_rng:8) run      [ ✓ ]
10:57:49  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:5, point_selects:20, order_rng:8) run      [ ✓ ]
10:58:03  Sysbench read only(distinct_rng:5, sum_rng:2, simple_rng:5, point_selects:30, order_rng:8) run      [ ✓ ]
10:58:25  Sysbench read only(distinct_rng:7, sum_rng:2, simple_rng:1, point_selects:10, order_rng:2) run      [ ✓ ]
10:58:36  Sysbench read only(distinct_rng:7, sum_rng:2, simple_rng:1, point_selects:20, order_rng:2) run      [ ✓ ]
10:58:47  Sysbench read only(distinct_rng:7, sum_rng:2, simple_rng:1, point_selects:30, order_rng:2) run      [ ✓ ]
10:58:58  Sysbench read only(distinct_rng:7, sum_rng:2, simple_rng:1, point_selects:10, order_rng:5) run      [ ✓ ]
10:59:08  Sysbench read only(distinct_rng:7, sum_rng:2, simple_rng:1, point_selects:20, order_rng:5) run      [ ✓ ]
10:59:18  Sysbench read only(distinct_rng:7, sum_rng:2, simple_rng:1, point_selects:30, order_rng:5) run      [ ✓ ]
10:59:28  Sysbench read only(distinct_rng:7, sum_rng:2, simple_rng:1, point_selects:10, order_rng:8) run      [ ✓ ]

