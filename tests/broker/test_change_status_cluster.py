#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing the cluster status commands."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestChangeClusterStatus(TestBrokerCommand):

    # This class is invoked after test_bind_esx_cluster, so we
    # know that we have a cluster (utecl1) which has 5 member hosts,
    # each of which are in "build" status.
    def test_100_BlockPromotion(self):
        command = ["change_status", "--hostname", "evh1.aqd-unittest.ms.com",
                                    "--buildstatus", "ready"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Warning: requested status was 'ready' but "
                              "resulting host status is 'almostready'.", command)

        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "Build Status: almostready", command)

    def test_110_PromoteCluster(self):
        command = ["change_status", "--cluster", "utecl1",
                   "--buildstatus", "ready"] + self.valid_just_tcm
        err = self.statustest(command)
        # FIXME: the number of changed templates is not deterministic, we have
        # to figure out why. Until then make the check less strict to allow
        # unrelated changes to be tested.
        # self.matchoutput(err, "5/5 template", command)
        self.searchoutput(err, r'[1-5]/[1-5] template', command)

        # the almostready host should now be promoted
        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: ready", command)

        # the build host should be unchanged
        command = "show host --hostname evh2.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: build", command)

    def test_120_BindDemotion(self):
        command = ["cluster",
                   "--hostname", "evh1.aqd-unittest.ms.com",
                   "--cluster", "utecl2"] + self.valid_just_tcm
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Notice: changing build status of host "
                              "evh1.aqd-unittest.ms.com from 'ready' to "
                              "'almostready' because ESX cluster utecl2's "
                              "state is 'build'.", command)

        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: almostready", command)

        # Put the host back and confirm it can move to ready
        self.successtest(["cluster",
                          "--hostname", "evh1.aqd-unittest.ms.com",
                          "--cluster", "utecl1"] + self.valid_just_tcm)
        self.successtest(["change_status",
                          "--hostname", "evh1.aqd-unittest.ms.com",
                          "--buildstatus", "ready"] + self.valid_just_tcm)

        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "Build Status: ready", command)

    def test_130_DemoteCluster(self):
        command = ["change_status", "--cluster", "utecl1",
                   "--buildstatus", "rebuild"] + self.valid_just_tcm
        err = self.statustest(command)
        # FIXME: the number of changed templates is not deterministic, we have
        # to figure out why. Until then make the check less strict to allow
        # unrelated changes to be tested.
        # self.matchoutput(err, "5/5 template", command)
        self.searchoutput(err, r'[1-5]/[1-5] template', command)

        # the ready host should be demoted
        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: almostready", command)

        # the build host should be unchanged
        command = "show host --hostname evh2.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: build", command)

    def test_140_DecoClusterFail(self):
        # add a vm to make change fail
        self.noouttest(["add", "machine", "--machine", "evm1",
                        "--cluster", "utecl1", "--model", "utmedium"])

        command = ["change_status", "--cluster", "utecl1", "--buildstatus",
                   "decommissioned"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot change state to decommissioned, as "
                         "ESX Cluster utecl1 has 1 VM(s).",
                         command)

        command = ["change_status", "--hostname", "evh1.aqd-unittest.ms.com",
                   "--buildstatus", "decommissioned"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot change state to decommissioned, as "
                         "ESX Cluster utecl1's state is not decommissioned.",
                         command)

        # remove temp vm
        self.noouttest(["del", "machine", "--machine", "evm1"])

    def test_145_DecoCluster(self):
        self.successtest(["change_status", "--cluster", "utecl1",
                          "--buildstatus", "decommissioned"] + self.valid_just_tcm)

        # all vmhosts must be decoed.
        for i in range(1, 5):
            command = "show host --hostname evh%d.aqd-unittest.ms.com" % i
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Build Status: decommissioned", command)

        # can't add vm
        command = ["add", "machine", "--machine", "evm1",
                   "--cluster", "utecl1", "--model", "utmedium"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot add virtual machines to decommissioned holders.",
                         command)

        # can't add host.
        command = ["cluster", "--hostname", "evh6.aqd-unittest.ms.com",
                   "--cluster", "utecl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot add hosts to decommissioned clusters.",
                         command)

        # revert status changes
        self.successtest(["change_status", "--cluster", "utecl1",
                          "--buildstatus", "rebuild"])

        for i in range(1, 5):
            self.successtest(["change_status",
                              "--hostname", "evh%d.aqd-unittest.ms.com" % i,
                              "--buildstatus", "rebuild"])

    def test_150_change_status_metacluster(self):
        command = ["change_status", "--metacluster", "utmc1",
                   "--buildstatus", "ready"]
        self.statustest(command)

    def test_155_verify_metacluster(self):
        command = ["show_metacluster", "--metacluster", "utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Build Status: ready", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestChangeClusterStatus)
    unittest.TextTestRunner(verbosity=2).run(suite)
