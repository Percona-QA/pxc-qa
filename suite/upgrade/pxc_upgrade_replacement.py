#!/usr/bin/env python3
import os
import sys

cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from base_test import *
from util import utility
from util import rqg_datagen


class PXCUpgrade(BaseTest):
    def __init__(self):
        super().__init__(vers=Version.LOWER)

    def rolling_replacement(self):
        # Start PXC cluster for rolling replacement test
        node = self.node3
        for i in [4, 5, 6]:
            node = pxc_startup.StartCluster.join_new_upgraded_node(node, i, debug)
            self.pxc_nodes.append(node)


utility.test_header("PXC Upgrade test : Upgrading from PXC-" + lower_version + " to PXC-" + upper_version)
utility.test_scenario_header("Rolling replacement upgrade without active workload")
upgrade_qa = PXCUpgrade()
upgrade_qa.start_pxc()
rqg_dataload = rqg_datagen.RQGDataGen(upgrade_qa.node1, debug)
rqg_dataload.pxc_dataload(workdir)
upgrade_qa.rolling_replacement()
upgrade_qa.shutdown_nodes()
