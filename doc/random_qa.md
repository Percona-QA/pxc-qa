Random QA script
-------------

This script is a small test and not a suite. pxc_util.py will start a 3 node cluster. we can configure it to start 3 node cluster with different options apart from the default.
We can also enable encryption options with `--encryption-run`

Random QA run log
--------------
```
$ python3 suite/random_qa/pxc_util.py --start

05:53:49  Startup sanity check                                                                                [ ✓ ]
05:53:49  Configuration file creation                                                                         [ ✓ ]
05:54:30  Initializing cluster                                                                                [ ✓ ]
05:55:30  Cluster startup                                                                                     [ ✓ ]
05:55:30  Database connection                                                                                 [ ✓ ]
05:55:30  PXC connection string                                                                               [ ✓ ]
	/dev/shm/qa/PXC_8.0.26/bin/mysql --user=root --socket=/dev/shm/qa/node1/mysql.sock
	/dev/shm/qa/PXC_8.0.26/bin/mysql --user=root --socket=/dev/shm/qa/node2/mysql.sock
	/dev/shm/qa/PXC_8.0.26/bin/mysql --user=root --socket=/dev/shm/qa/node3/mysql.sock



$ python3 qa_framework.py --testname=suite/random_qa/random_mysqld_option_test.py
------------------------------
PXC Random MySQLD options test
------------------------------
06:08:01  Startup sanity check                                                                                [ ✓ ]
06:08:01  Configuration file creation                                                                         [ ✓ ]
06:08:01  Added random mysqld option: abort-slave-event-count=0
                                              [ ✓ ]
06:08:41  Initializing cluster                                                                                [ ✓ ]
06:09:41  Cluster startup                                                                                     [ ✓ ]
06:09:41  Database connection                                                                                 [ ✓ ]
06:09:41  Sysbench run sanity check                                                                           [ ✓ ]
06:09:46  Sysbench data load                                                                                  [ ✓ ]
06:09:56  Creating prepared statements                                                                        [ ✓ ]
06:09:59  Sample data load                                                                                    [ ✓ ]
06:10:12  PXC: shutting down cluster node3                                                                    [ ✓ ]
06:10:26  PXC: shutting down cluster node2                                                                    [ ✓ ]
06:10:40  PXC: shutting down cluster node1                                                                    [ ✓ ]
06:10:40  Startup sanity check                                                                                [ ✓ ]
06:10:40  Configuration file creation                                                                         [ ✓ ]
06:10:40  Added random mysqld option: abort-slave-event-count=2
                                              [ ✓ ]
06:11:20  Initializing cluster                                                                                [ ✓ ]
06:12:18  Cluster startup                                                                                     [ ✓ ]
06:12:18  Database connection                                                                                 [ ✓ ]
06:12:18  Sysbench run sanity check                                                                           [ ✓ ]
06:12:23  Sysbench data load                                                                                  [ ✓ ]
06:12:34  Creating prepared statements                                                                        [ ✓ ]
06:12:37  Sample data load                                                                                    [ ✓ ]
06:12:51  PXC: shutting down cluster node3                                                                    [ ✓ ]
06:13:05  PXC: shutting down cluster node2                                                                    [ ✓ ]
06:13:19  PXC: shutting down cluster node1                                                                    [ ✓ ]
06:13:19  Startup sanity check                                                                                [ ✓ ]
06:13:19  Configuration file creation                                                                         [ ✓ ]
06:13:19  Added random mysqld option: activate-all-roles-on-login=1
                                          [ ✓ ]
06:13:59  Initializing cluster                                                                                [ ✓ ]
06:14:58  Cluster startup                                                                                     [ ✓ ]
06:14:58  Database connection                                                                                 [ ✓ ]
06:14:58  Sysbench run sanity check                                                                           [ ✓ ]
06:15:02  Sysbench data load                                                                                  [ ✓ ]
06:15:13  Creating prepared statements                                                                        [ ✓ ]
06:15:16  Sample data load                                                                                    [ ✓ ]
06:15:30  PXC: shutting down cluster node3                                                                    [ ✓ ]
06:15:45  PXC: shutting down cluster node2                                                                    [ ✓ ]
06:15:59  PXC: shutting down cluster node1                                                                    [ ✓ ]
06:15:59  Startup sanity check                                                                                [ ✓ ]
06:15:59  Configuration file creation                                                                         [ ✓ ]
06:15:59  Added random mysqld option: activate-all-roles-on-login=0
                                          [ ✓ ]
06:16:39  Initializing cluster                                                                                [ ✓ ]
06:17:38  Cluster startup                                                                                     [ ✓ ]
06:17:38  Database connection                                                                                 [ ✓ ]
06:17:38  Sysbench run sanity check                                                                           [ ✓ ]
06:17:42  Sysbench data load                                                                                  [ ✓ ]
06:17:54  Creating prepared statements                                                                        [ ✓ ]
06:17:57  Sample data load                                                                                    [ ✓ ]
06:18:11  PXC: shutting down cluster node3                                                                    [ ✓ ]
06:18:26  PXC: shutting down cluster node2                                                                    [ ✓ ]
06:18:40  PXC: shutting down cluster node1                                                                    [ ✓ ]
06:18:40  Startup sanity check                                                                                [ ✓ ]
06:18:40  Configuration file creation                                                                         [ ✓ ]
06:18:40  Added random mysqld option: allow-suspicious-udfs=1
                                                [ ✓ ]
06:19:21  Initializing cluster                                                                                [ ✓ ]
06:20:20  Cluster startup                                                                                     [ ✓ ]
06:20:20  Database connection                                                                                 [ ✓ ]
06:20:20  Sysbench run sanity check                                                                           [ ✓ ]
06:20:24  Sysbench data load                                                                                  [ ✓ ]
06:20:34  Creating prepared statements                                                                        [ ✓ ]
06:20:38  Sample data load                                                                                    [ ✓ ]
06:20:52  PXC: shutting down cluster node3                                                                    [ ✓ ]
06:21:07  PXC: shutting down cluster node2                                                                    [ ✓ ]
06:21:21  PXC: shutting down cluster node1                                                                    [ ✓ ]
06:21:21  Startup sanity check                                                                                [ ✓ ]
06:21:21  Configuration file creation                                                                         [ ✓ ]
06:21:21  Added random mysqld option: allow-suspicious-udfs=0
                                                [ ✓ ]
06:22:01  Initializing cluster                                                                                [ ✓ ]
06:23:00  Cluster startup                                                                                     [ ✓ ]
06:23:00  Database connection                                                                                 [ ✓ ]
06:23:00  Sysbench run sanity check                                                                           [ ✓ ]
06:23:04  Sysbench data load                                                                                  [ ✓ ]
06:23:15  Creating prepared statements                                                                        [ ✓ ]
06:23:18  Sample data load                                                                                    [ ✓ ]
06:23:32  PXC: shutting down cluster node3                                                                    [ ✓ ]
06:23:46  PXC: shutting down cluster node2                                                                    [ ✓ ]
06:24:00  PXC: shutting down cluster node1                                                                    [ ✓ ]
06:24:00  Startup sanity check                                                                                [ ✓ ]
06:24:00  Configuration file creation                                                                         [ ✓ ]
06:24:00  Added random mysqld option: archive=1
                                                              [ ✓ ]
06:24:40  Initializing cluster                                                                                [ ✓ ]
06:25:37  Cluster startup                                                                                     [ ✓ ]
06:25:37  Database connection                                                                                 [ ✓ ]
06:25:37  Sysbench run sanity check                                                                           [ ✓ ]
06:25:42  Sysbench data load                                                                                  [ ✓ ]
06:25:53  Creating prepared statements                                                                        [ ✓ ]
06:25:56  Sample data load                                                                                    [ ✓ ]
06:26:09  PXC: shutting down cluster node3                                                                    [ ✓ ]
06:26:24  PXC: shutting down cluster node2                                                                    [ ✓ ]
06:26:38  PXC: shutting down cluster node1                                                                    [ ✓ ]
06:26:38  Startup sanity check                                                                                [ ✓ ]
06:26:38  Configuration file creation                                                                         [ ✓ ]
06:26:38  Added random mysqld option: archive=0
                                                              [ ✓ ]
[...]
```

