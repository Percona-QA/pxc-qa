#!/usr/bin/env python3
import os
import sys
import itertools

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)

from base_test import *
from util import utility

if args.encryption_run is True:
    pstress_extra = ""
else:
    pstress_extra = "--no-encryption"


class RandomPstressQA(BaseTest):
    def __init__(self):
        super().__init__(my_extra='--max-connections=1500')

    def data_load(self):
        # pstress random load
        threads = [64, 1024]  # 512, 16
        tables = [32, 128]  # 64, 16
        records = [100, 500, 1000]  # 200
        seeds = [1000]  # 500, 100
        for thread, table, record, seed in \
                itertools.product(threads, tables, records, seeds):
            self.start_pxc()
            queries = ["drop database if exists test", "create database test"]
            self.node1.execute_queries(queries)
            utility_cmd.pstress_run(socket=self.node1.get_socket(), db=db, seed=seed, tables=table,
                                    threads=table, records=record, pstress_extra=pstress_extra,
                                    workdir=workdir)


utility.test_header("PXC Random PSTRESS QA")
random_pstress_qa = RandomPstressQA()
random_pstress_qa.data_load()
