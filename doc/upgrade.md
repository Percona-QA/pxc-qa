Upgrade QA script
---------------------
This suite tests Percona XtraDB Cluster upgrade. Configure lower and upper PXC
tarball paths in [config.ini](../config.ini) under the `[upgrade]` section.
Encryption can be enabled with `--encryption-run`.

Running tests
-------------

Run the full upgrade suite:

```bash
python3 qa_framework.py --suites=upgrade
```

Run a single upgrade test:

```bash
python3 qa_framework.py --tests=upgrade.pxc_upgrade.py
```

Upgrade suite log
------------------
```
$
PXC Upgrade test : Upgrading from PXC-5.6.37 to PXC-5.6.44
------------------------------------------------------------------------------
06:51:46  Startup sanity check                                                                                [ ✔ ]
06:51:46  Configuration file creation                                                                         [ ✔ ]
06:52:35  Initializing cluster                                                                                [ ✔ ]
06:53:12  Cluster startup                                                                                     [ ✔ ]
06:53:12  Database connection                                                                                 [ ✔ ]
06:53:18  RQG data load                                                                                       [ ✔ ]
06:53:25  RQG data load                                                                                       [ ✔ ]
06:53:25  RQG data load                                                                                       [ ✔ ]
06:54:06  RQG data load                                                                                       [ ✔ ]
06:54:06  Sysbench run sanity check                                                                           [ ✔ ]
06:54:08  Sysbench data load                                                                                  [ ✔ ]
06:54:12  Shutdown cluster node3 for upgrade testing                                                          [ ✔ ]
06:54:14  Node startup is successful                                                                          [ ✔ ]
06:54:15  Cluster node3 upgrade is successful                                                                 [ ✔ ]
06:54:18  Shutdown cluster node3 after upgrade run                                                            [ ✔ ]
06:54:23  Starting cluster node3 after upgrade run                                                            [ ✔ ]
06:54:26  Node startup is successful                                                                          [ ✔ ]
06:54:30  Shutdown cluster node2 for upgrade testing                                                          [ ✔ ]
06:54:32  Node startup is successful                                                                          [ ✔ ]
06:54:33  Cluster node2 upgrade is successful                                                                 [ ✔ ]
06:54:35  Shutdown cluster node2 after upgrade run                                                            [ ✔ ]
06:54:40  Starting cluster node2 after upgrade run                                                            [ ✔ ]
06:54:43  Node startup is successful                                                                          [ ✔ ]
06:54:47  Shutdown cluster node1 for upgrade testing                                                          [ ✔ ]
06:54:49  Node startup is successful                                                                          [ ✔ ]
06:54:51  Cluster node1 upgrade is successful                                                                 [ ✔ ]
06:54:53  Shutdown cluster node1 after upgrade run                                                            [ ✔ ]
06:54:58  Starting cluster node1 after upgrade run                                                            [ ✔ ]
06:55:01  Node startup is successful                                                                          [ ✔ ]
06:55:07  pt-table-checksum error code : At least one diff was found                                          [ ✘ ]
$
```
