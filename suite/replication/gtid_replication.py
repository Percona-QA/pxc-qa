#!/usr/bin/env python3
import os
import sys

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from suite.replication.replication import SetupReplication
from util import utility


class SetupGtidReplication(SetupReplication):
    def __init__(self):
        super().__init__(rpl_type=utility.RplType.GTID)


if __name__ == '__main__':

    gtid_replication_run = SetupGtidReplication()

    utility.test_header("GTID PXC->PS async replication")
    gtid_replication_run.replication_testcase(is_pxc_source=True)
    utility.test_header("GTID PS->PXC async replication")
    gtid_replication_run.replication_testcase()

    if int(version) > int("050700"):
        utility.test_header("GTID PS1->PXC, PS2->PXC Multi source replication")
        gtid_replication_run.replication_testcase(2, comment='msr')
        utility.test_header("GTID PS->PXC multi threaded async replication")
        gtid_replication_run.replication_testcase(comment='mta')
