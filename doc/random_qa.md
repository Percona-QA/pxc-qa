Random QA script
-------------

This script is a small test and not a suite. pxc_util.py will start a 3 node cluster. We can configure it to start 3 node cluster with different options apart from the default. 
If we need to start cluster with `innodb-buffer-pool-size=128M` then we can edit pxc_util.py as below 
result = server_startup.start_cluster('--innodb-buffer-pool-size=128M ')
We can also enable encryption options with `--encryption-run`
We can also enable debug options with `--debug`

Random QA run log
--------------
```
$ python3 suite/random_qa/pxc_util.py --start --debug

13:26:04  Startup sanity check                                                                                [ ✓ ]
13:26:04  Configuration file creation                                                                         [ ✓ ]
/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysqld --no-defaults  --initialize-insecure  --basedir=/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17 --datadir=/dev/shm/qa/node1 > /dev/shm/qa/log/startup1.log 2>&1
/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysqld --no-defaults  --initialize-insecure  --basedir=/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17 --datadir=/dev/shm/qa/node2 > /dev/shm/qa/log/startup2.log 2>&1
/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysqld --no-defaults  --initialize-insecure  --basedir=/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17 --datadir=/dev/shm/qa/node3 > /dev/shm/qa/log/startup3.log 2>&1
13:26:10  Initializing cluster                                                                                [ ✓ ]
/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysqld --defaults-file=/dev/shm/qa/conf/node1.cnf --datadir=/dev/shm/qa/node1 --basedir=/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17 --innodb-buffer-pool-size=128M  --wsrep-provider=/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/lib/libgalera_smm.so --wsrep-new-cluster --log-error=/dev/shm/qa/log/node1.err > /dev/shm/qa/log/node1.err 2>&1 &
/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysql --user=root --socket=/dev/shm/qa/node1/mysql.sock -Bse"delete from mysql.user where user='';" > /dev/null 2>&1
/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysqld --defaults-file=/dev/shm/qa/conf/node2.cnf --datadir=/dev/shm/qa/node2 --basedir=/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17 --innodb-buffer-pool-size=128M  --wsrep-provider=/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/lib/libgalera_smm.so --log-error=/dev/shm/qa/log/node2.err > /dev/shm/qa/log/node2.err 2>&1 &
/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysql --user=root --socket=/dev/shm/qa/node2/mysql.sock -Bse"delete from mysql.user where user='';" > /dev/null 2>&1
/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysqld --defaults-file=/dev/shm/qa/conf/node3.cnf --datadir=/dev/shm/qa/node3 --basedir=/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17 --innodb-buffer-pool-size=128M  --wsrep-provider=/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/lib/libgalera_smm.so --log-error=/dev/shm/qa/log/node3.err > /dev/shm/qa/log/node3.err 2>&1 &
/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysql --user=root --socket=/dev/shm/qa/node3/mysql.sock -Bse"delete from mysql.user where user='';" > /dev/null 2>&1
13:26:57  Cluster startup                                                                                     [ ✓ ]
13:26:57  Database connection                                                                                 [ ✓ ]
/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysql --user=root --socket=/dev/shm/qa/node1/mysql.sock -e'drop database if exists test ; create database test ;' > /dev/null 2>&1
13:26:57  PXC connection string                                                                               [ ✓ ]
	/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysql --user=root --socket=/dev/shm/qa/node1/mysql.sock
	/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysql --user=root --socket=/dev/shm/qa/node2/mysql.sock
	/dev/shm/qa/Percona-XtraDB-Cluster_8.0.26-16.1_Linux.x86_64.glibc2.17/bin/mysql --user=root --socket=/dev/shm/qa/node3/mysql.sock


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


$ python3 qa_framework.py --testname=suite/random_qa/pstress_crash_recovery_qa.py
--------------------
PXC Random PSTRESS QA
--------------------
06:32:02  Startup sanity check                                                                                [ ✓ ]
06:32:02  Configuration file creation                                                                         [ ✓ ]
06:32:43  Initializing cluster                                                                                [ ✓ ]
06:33:42  Cluster startup                                                                                     [ ✓ ]
06:33:42  Database connection                                                                                 [ ✓ ]
06:33:42  PSTRESS RUN command : /home/vagrant/pstress/src/pstress-pxc --database=test --threads=10 --logdir=/dev/shm/qa/log --log-all-queries --log-failed-queries --user=root --socket=/dev/shm/qa/node1/mysql.sock --seed 1000 --tables 5 --records 10 --no-encryption --seconds 30 --grammar-file /home/vagrant/pstress/src/grammar.sql --step 1 > /dev/shm/qa/log/pstress_run.log[ ✓ ]
06:34:25  Cluster restart is successful                                                                       [ ✓ ]
06:34:57  Cluster restart is successful                                                                       [ ✓ ]
06:35:26  Cluster restart is successful                                                                       [ ✓ ]
06:35:26  PSTRESS RUN command : /home/vagrant/pstress/src/pstress-pxc --database=test --threads=10 --logdir=/dev/shm/qa/log --log-all-queries --log-failed-queries --user=root --socket=/dev/shm/qa/node1/mysql.sock --seed 1000 --tables 5 --records 10 --no-encryption --seconds 30 --grammar-file /home/vagrant/pstress/src/grammar.sql --step 2 > /dev/shm/qa/log/pstress_run.log[ ✓ ]
06:36:08  Cluster restart is successful                                                                       [ ✓ ]
06:36:38  Cluster restart is successful                                                                       [ ✓ ]
06:37:08  Cluster restart is successful                                                                       [ ✓ ]
06:37:08  PSTRESS RUN command : /home/vagrant/pstress/src/pstress-pxc --database=test --threads=10 --logdir=/dev/shm/qa/log --log-all-queries --log-failed-queries --user=root --socket=/dev/shm/qa/node1/mysql.sock --seed 1000 --tables 5 --records 10 --no-encryption --seconds 30 --grammar-file /home/vagrant/pstress/src/grammar.sql --step 3 > /dev/shm/qa/log/pstress_run.log[ ✓ ]
06:37:48  Cluster restart is successful                                                                       [ ✓ ]
06:38:18  Cluster restart is successful                                                                       [ ✓ ]
06:38:49  Cluster restart is successful                                                                       [ ✓ ]
06:38:49  PSTRESS RUN command : /home/vagrant/pstress/src/pstress-pxc --database=test --threads=10 --logdir=/dev/shm/qa/log --log-all-queries --log-failed-queries --user=root --socket=/dev/shm/qa/node1/mysql.sock --seed 1000 --tables 5 --records 10 --no-encryption --seconds 30 --grammar-file /home/vagrant/pstress/src/grammar.sql --step 4 > /dev/shm/qa/log/pstress_run.log[ ✓ ]
06:39:29  Cluster restart is successful                                                                       [ ✓ ]
06:39:59  Cluster restart is successful                                                                       [ ✓ ]
06:40:31  Cluster restart is successful                                                                       [ ✓ ]
06:40:31  PSTRESS RUN command : /home/vagrant/pstress/src/pstress-pxc --database=test --threads=10 --logdir=/dev/shm/qa/log --log-all-queries --log-failed-queries --user=root --socket=/dev/shm/qa/node1/mysql.sock --seed 1000 --tables 5 --records 10 --no-encryption --seconds 30 --grammar-file /home/vagrant/pstress/src/grammar.sql --step 5 > /dev/shm/qa/log/pstress_run.log[ ✓ ]
06:41:11  Cluster restart is successful                                                                       [ ✓ ]
06:41:40  Cluster restart is successful                                                                       [ ✓ ]
06:42:11  Cluster restart is successful                                                                       [ ✓ ]
06:42:11  PSTRESS RUN command : /home/vagrant/pstress/src/pstress-pxc --database=test --threads=10 --logdir=/dev/shm/qa/log --log-all-queries --log-failed-queries --user=root --socket=/dev/shm/qa/node1/mysql.sock --seed 1000 --tables 5 --records 10 --no-encryption --seconds 30 --grammar-file /home/vagrant/pstress/src/grammar.sql --step 6 > /dev/shm/qa/log/pstress_run.log[ ✓ ]


$ python3 qa_framework.py --testname=suite/random_qa/pstress_random_qa.py

--------------------
PXC Random PSTRESS QA
--------------------
06:53:59  Startup sanity check                                                                                [ ✓ ]
06:53:59  Configuration file creation                                                                         [ ✓ ]
06:54:39  Initializing cluster                                                                                [ ✓ ]
06:55:38  Cluster startup                                                                                     [ ✓ ]
06:55:38  Database connection                                                                                 [ ✓ ]
06:55:38  PSTRESS RUN command : /home/vagrant/pstress/src/pstress-pxc --database=test --threads=16 --logdir=/dev/shm/qa/log --log-all-queries --log-failed-queries --user=root --socket=/dev/shm/qa/node1/mysql.sock --seed 100 --tables 16 --no-encryption --seconds 30  --grammar-file /home/vagrant/pstress/src/grammar.sql --records 100> /dev/shm/qa/log/pstress_run.log[ ✓ ]
06:56:27  Startup sanity check                                                                                [ ✓ ]
06:56:28  Configuration file creation                                                                         [ ✓ ]
06:57:10  Initializing cluster                                                                                [ ✓ ]
06:58:11  Cluster startup                                                                                     [ ✓ ]
06:58:11  Database connection                                                                                 [ ✓ ]
06:58:11  PSTRESS RUN command : /home/vagrant/pstress/src/pstress-pxc --database=test --threads=16 --logdir=/dev/shm/qa/log --log-all-queries --log-failed-queries --user=root --socket=/dev/shm/qa/node1/mysql.sock --seed 500 --tables 16 --no-encryption --seconds 30  --grammar-file /home/vagrant/pstress/src/grammar.sql --records 100> /dev/shm/qa/log/pstress_run.log[ ✓ ]
06:58:55  Startup sanity check                                                                                [ ✓ ]
06:58:55  Configuration file creation                                                                         [ ✓ ]
06:59:36  Initializing cluster                                                                                [ ✓ ]
07:00:37  Cluster startup                                                                                     [ ✓ ]
07:00:37  Database connection                                                                                 [ ✓ ]
07:00:37  PSTRESS RUN command : /home/vagrant/pstress/src/pstress-pxc --database=test --threads=16 --logdir=/dev/shm/qa/log --log-all-queries --log-failed-queries --user=root --socket=/dev/shm/qa/node1/mysql.sock --seed 1000 --tables 16 --no-encryption --seconds 30  --grammar-file /home/vagrant/pstress/src/grammar.sql --records 100> /dev/shm/qa/log/pstress_run.log[ ✓ ]
07:01:23  Startup sanity check                                                                                [ ✓ ]
07:01:23  Configuration file creation                                                                         [ ✓ ]
07:02:05  Initializing cluster                                                                                [ ✓ ]
07:03:04  Cluster startup                                                                                     [ ✓ ]
07:03:04  Database connection                                                                                 [ ✓ ]
07:03:04  PSTRESS RUN command : /home/vagrant/pstress/src/pstress-pxc --database=test --threads=16 --logdir=/dev/shm/qa/log --log-all-queries --log-failed-queries --user=root --socket=/dev/shm/qa/node1/mysql.sock --seed 100 --tables 16 --no-encryption --seconds 30  --grammar-file /home/vagrant/pstress/src/grammar.sql --records 500> /dev/shm/qa/log/pstress_run.log[ ✓ ]
[...]
```

