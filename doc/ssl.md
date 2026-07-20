SSL QA script
-------------

This suite enables SSL configurations for SST, data transfer, and client-server
connections. Encryption can be enabled with `--encryption-run`.

Running tests
-------------

Run the full SSL suite:

```bash
python3 qa_framework.py --suites=ssl
```

Run the encryption test only:

```bash
python3 qa_framework.py --tests=ssl.encryption_qa.py --encryption-run
```

SSL QA run log
--------------
```
$ python3 qa_framework.py --suites=ssl

PXC SSL test
--------------
07:27:59  Startup sanity check                                                                                [ ✔ ]
07:27:59  SSL Configuration                                                                                   [ ✔ ]
07:27:59  Configuration file creation                                                                         [ ✔ ]
07:28:34  Initializing cluster                                                                                [ ✔ ]
07:28:55  Cluster startup                                                                                     [ ✔ ]
07:28:55  Database connection                                                                                 [ ✔ ]
07:28:55  SSL QA sysbench run sanity check                                                                    [ ✔ ]
07:28:57  SSL QA sysbench data load                                                                           [ ✔ ]
07:28:57  SSL QA sample DB creation                                                                           [ ✔ ]
07:28:59  SSL QA sample data load                                                                             [ ✔ ]
07:29:04  RQG data load                                                                                       [ ✔ ]
07:29:04  SSL QA table test.sbtest1 checksum between nodes                                                    [ ✔ ]
07:29:04  SSL QA table pxc_dataload_db.t1 checksum between nodes                                              [ ✔ ]
07:29:05  pt-table-checksum run status                                                                        [ ✔ ]
$
```
