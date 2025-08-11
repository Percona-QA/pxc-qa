#!/usr/bin/env python3
import os
import random
import sys

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
        super().__init__()

    def data_load(self):
        # pstress crash recovery qa
        self.start_pxc()
        queries = ["drop database if exists test", "create database test"]
        self.node1.execute_queries(queries)
        n = random.randint(10000, 99999)
        for i in range(1, 10):
            utility_cmd.pstress_run(socket=self.node1.get_socket(), db=db, seed=n, step_num=i,
                                    pstress_extra=pstress_extra, workdir=workdir)
            # kill existing mysqld process
            utility_cmd.kill_cluster_nodes()
            utility_cmd.restart_cluster(self.pxc_nodes)


utility.test_header("PXC Crash Recovery PSTRESS QA")
random_pstress_qa = RandomPstressQA()
random_pstress_qa.data_load()
