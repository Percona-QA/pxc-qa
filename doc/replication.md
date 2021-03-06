Replication QA script
---------------------
This suite will cover following replication testcases. To enable encryption options you should use 
the argument `--encryption-run` with pxc qa framework.

* PXC node as master and PS node as slave (GTID and Non-GTID)
* PXC node as slave and PS node as master (GTID and Non-GTID)
* Multi source replication - PXC node act as multi master slave (GTID and Non-GTID)
* Multi thread replication - PXC node act as multi thread slave (GTID and Non-GTID)
* Configure replication using Percona Xtrabackup

Replication suite log
---------------------
```
$ python3 pxc_qa_framework.py  --suite=replication

GTID PXC Node as Master and PS node as Slave
----------------------------------------------
07:05:31  PXC: Startup sanity check                                                                           [ ✔ ]
07:05:31  PXC: Configuration file creation                                                                    [ ✔ ]
07:06:06  PXC: Initializing cluster                                                                           [ ✔ ]
07:06:06  PXC: Adding custom configuration                                                                    [ ✔ ]
07:06:27  PXC: Cluster startup                                                                                [ ✔ ]
07:06:27  PXC: Database connection                                                                            [ ✔ ]
07:06:27  PS: Startup sanity check                                                                            [ ✔ ]
07:06:27  PS: Configuration file creation                                                                     [ ✔ ]
07:06:27  PS: Adding custom configuration                                                                     [ ✔ ]
07:06:45  PS: Initializing cluster                                                                            [ ✔ ]
07:06:47  PS: Cluster startup                                                                                 [ ✔ ]
07:06:47  PS: Database connection                                                                             [ ✔ ]
07:06:47  Initiated replication                                                                               [ ✔ ]
07:06:47  PXC: Replication QA sysbench run sanity check                                                       [ ✔ ]
07:06:49  PXC: Replication QA sysbench data load                                                              [ ✔ ]
07:06:49  PXC: Replication QA sample DB creation                                                              [ ✔ ]
07:06:51  PXC: Replication QA sample data load                                                                [ ✔ ]
07:06:57  RQG data load                                                                                       [ ✔ ]
07:07:08  RQG data load                                                                                       [ ✔ ]
07:07:15  RQG data load                                                                                       [ ✔ ]
07:07:44  RQG data load                                                                                       [ ✔ ]
07:08:04  RQG data load                                                                                       [ ✔ ]
07:08:14  RQG data load                                                                                       [ ✔ ]
07:08:20  RQG data load                                                                                       [ ✔ ]
07:08:21  RQG data load                                                                                       [ ✔ ]
07:08:51  RQG data load                                                                                       [ ✔ ]
07:08:54  RQG data load                                                                                       [ ✔ ]
07:08:54  PS: IO thread slave status                                                                          [ ✔ ]
07:08:54  PS: SQL thread slave status                                                                         [ ✔ ]

GTID PXC Node as Slave and PS node as Master
----------------------------------------------
07:08:55  PXC: Startup sanity check                                                                           [ ✔ ]
07:08:55  PXC: Configuration file creation                                                                    [ ✔ ]
07:09:32  PXC: Initializing cluster                                                                           [ ✔ ]
07:09:32  PXC: Adding custom configuration                                                                    [ ✔ ]
07:09:54  PXC: Cluster startup                                                                                [ ✔ ]
07:09:54  PXC: Database connection                                                                            [ ✔ ]
07:09:54  PS: Startup sanity check                                                                            [ ✔ ]
07:09:54  PS: Configuration file creation                                                                     [ ✔ ]
07:09:54  PS: Adding custom configuration                                                                     [ ✔ ]
07:10:12  PS: Initializing cluster                                                                            [ ✔ ]
07:10:14  PS: Cluster startup                                                                                 [ ✔ ]
07:10:14  PS: Database connection                                                                             [ ✔ ]
07:10:14  Initiated replication                                                                               [ ✔ ]
07:10:14  PS: Replication QA sysbench run sanity check                                                        [ ✔ ]
07:10:15  PS: Replication QA sysbench data load                                                               [ ✔ ]
07:10:15  PS: Replication QA sample DB creation                                                               [ ✔ ]
07:10:16  PS: Replication QA sample data load                                                                 [ ✔ ]
07:10:18  RQG data load                                                                                       [ ✔ ]
07:10:27  RQG data load                                                                                       [ ✔ ]
07:10:32  RQG data load                                                                                       [ ✔ ]
07:10:53  RQG data load                                                                                       [ ✔ ]
07:11:08  RQG data load                                                                                       [ ✔ ]
07:11:16  RQG data load                                                                                       [ ✔ ]
07:11:18  RQG data load                                                                                       [ ✔ ]
07:11:18  RQG data load                                                                                       [ ✔ ]
07:11:39  RQG data load                                                                                       [ ✔ ]
07:11:42  RQG data load                                                                                       [ ✔ ]
07:11:42  PXC: IO thread slave status                                                                         [ ✔ ]
07:11:42  PXC: SQL thread slave status                                                                        [ ✔ ]

Setup replication using Percona Xtrabackup
------------------------------------------
07:11:42  PXC: Startup sanity check                                                                           [ ✔ ]
07:11:42  PXC: Configuration file creation                                                                    [ ✔ ]
07:12:19  PXC: Initializing cluster                                                                           [ ✔ ]
07:12:19  PXC: Adding custom configuration                                                                    [ ✔ ]
07:12:40  PXC: Cluster startup                                                                                [ ✔ ]
07:12:40  PXC: Database connection                                                                            [ ✔ ]
07:12:40  PXC: Replication QA sysbench run sanity check                                                       [ ✔ ]
07:12:42  PXC: Replication QA sysbench data load                                                              [ ✔ ]
07:12:42  PXC: Replication QA sample DB creation                                                              [ ✔ ]
07:12:43  PXC: Replication QA sample data load                                                                [ ✔ ]
07:12:53  PS: Startup sanity check                                                                            [ ✔ ]
07:12:53  PS: Configuration file creation                                                                     [ ✔ ]
07:12:53  PS: Adding custom configuration                                                                     [ ✔ ]
07:12:55  PS: Cluster startup                                                                                 [ ✔ ]
07:12:55  PS: Database connection                                                                             [ ✔ ]
07:12:55  Initiated replication                                                                               [ ✔ ]
07:12:55  PS: IO thread slave status                                                                          [ ✔ ]
07:12:55  PS: SQL thread slave status                                                                         [ ✔ ]

NON-GTID PXC Node as Master and PS node as Slave
----------------------------------------------
07:12:55  PXC: Startup sanity check                                                                           [ ✔ ]
07:12:55  PXC: Configuration file creation                                                                    [ ✔ ]
07:13:30  PXC: Initializing cluster                                                                           [ ✔ ]
07:13:30  PXC: Adding custom configuration                                                                    [ ✔ ]
07:13:51  PXC: Cluster startup                                                                                [ ✔ ]
07:13:51  PXC: Database connection                                                                            [ ✔ ]
07:13:51  PS: Startup sanity check                                                                            [ ✔ ]
07:13:51  PS: Configuration file creation                                                                     [ ✔ ]
07:13:51  PS: Adding custom configuration                                                                     [ ✔ ]
07:14:08  PS: Initializing cluster                                                                            [ ✔ ]
07:14:10  PS: Cluster startup                                                                                 [ ✔ ]
07:14:10  PS: Database connection                                                                             [ ✔ ]
07:14:10  Initiated replication                                                                               [ ✔ ]
07:14:11  PXC: Replication QA sysbench run sanity check                                                       [ ✔ ]
07:14:12  PXC: Replication QA sysbench data load                                                              [ ✔ ]
07:14:12  PXC: Replication QA sample DB creation                                                              [ ✔ ]
07:14:15  PXC: Replication QA sample data load                                                                [ ✔ ]
07:14:20  RQG data load                                                                                       [ ✔ ]
07:14:31  RQG data load                                                                                       [ ✔ ]
07:14:38  RQG data load                                                                                       [ ✔ ]
07:15:06  RQG data load                                                                                       [ ✔ ]
07:15:24  RQG data load                                                                                       [ ✔ ]
07:15:33  RQG data load                                                                                       [ ✔ ]
07:15:39  RQG data load                                                                                       [ ✔ ]
07:15:39  RQG data load                                                                                       [ ✔ ]
07:16:08  RQG data load                                                                                       [ ✔ ]
07:16:12  RQG data load                                                                                       [ ✔ ]
07:16:12  PS: IO thread slave status                                                                          [ ✔ ]
07:16:12  PS: SQL thread slave status                                                                         [ ✔ ]

NON-GTID PXC Node as Slave and PS node as Master
----------------------------------------------
07:16:12  PXC: Startup sanity check                                                                           [ ✔ ]
07:16:12  PXC: Configuration file creation                                                                    [ ✔ ]
07:16:49  PXC: Initializing cluster                                                                           [ ✔ ]
07:16:49  PXC: Adding custom configuration                                                                    [ ✔ ]
07:17:11  PXC: Cluster startup                                                                                [ ✔ ]
07:17:11  PXC: Database connection                                                                            [ ✔ ]
07:17:11  PS: Startup sanity check                                                                            [ ✔ ]
07:17:11  PS: Configuration file creation                                                                     [ ✔ ]
07:17:11  PS: Adding custom configuration                                                                     [ ✔ ]
07:17:29  PS: Initializing cluster                                                                            [ ✔ ]
07:17:31  PS: Cluster startup                                                                                 [ ✔ ]
07:17:31  PS: Database connection                                                                             [ ✔ ]
07:17:31  Initiated replication                                                                               [ ✔ ]
07:17:31  PS: Replication QA sysbench run sanity check                                                        [ ✔ ]
07:17:32  PS: Replication QA sysbench data load                                                               [ ✔ ]
07:17:32  PS: Replication QA sample DB creation                                                               [ ✔ ]
07:17:33  PS: Replication QA sample data load                                                                 [ ✔ ]
07:17:35  RQG data load                                                                                       [ ✔ ]
07:17:44  RQG data load                                                                                       [ ✔ ]
07:17:49  RQG data load                                                                                       [ ✔ ]
07:18:10  RQG data load                                                                                       [ ✔ ]
07:18:25  RQG data load                                                                                       [ ✔ ]
07:18:33  RQG data load                                                                                       [ ✔ ]
07:18:35  RQG data load                                                                                       [ ✔ ]
07:18:35  RQG data load                                                                                       [ ✔ ]
07:18:56  RQG data load                                                                                       [ ✔ ]
07:18:59  RQG data load                                                                                       [ ✔ ]
07:18:59  PXC: IO thread slave status                                                                         [ ✔ ]
07:18:59  PXC: SQL thread slave status                                                                        [ ✔ ]
$
````
