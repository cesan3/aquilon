#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing how a logical DB might be configured."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUsecaseDatabase(TestBrokerCommand):

    def test_00_standalone_single_dbserver(self):
        command = ["add_filesystem", "--filesystem=gnr.0", "--type=ext3",
                   "--mountpoint=/d/d1/utdb1",
                   "--blockdevice=/dev/vx/dg.0/gnr.0",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=rw",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["add_application", "--application=nydb1", "--eonid=42",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["reconfigure", "--personality=sybase-test",
                   "--buildstatus=rebuild",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource: nydb1 (application)", command)
        self.matchoutput(out, "Resource: gnr.0 (filesystem)", command)

        command = ["cat", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "'/system/resources/filesystem' = push(create(\"resource/filesystem/host/server1.aqd-unittest.ms.com/gnr.0/config\"))", command)
        self.matchoutput(out, "'/system/resources/application' = push(create(\"resource/application/host/server1.aqd-unittest.ms.com/nydb1/config\"))", command)

    def test_10_standalone_two_dbserver(self):
        command = ["add_filesystem", "--filesystem=gnr.1", "--type=ext3",
                   "--mountpoint=/d/d1/utdb2",
                   "--blockdevice=/dev/vx/dg.0/gnr.1",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=rw",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["add_application", "--application=utdb2", "--eonid=42",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["compile", "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["compile", "--hostname=server1.aqd-unittest.ms.com",
                   "--pancdebug"]
        self.successtest(command)

        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource: nydb1 (application)", command)
        self.matchoutput(out, "Resource: gnr.0 (filesystem)", command)
        self.matchoutput(out, "Resource: utdb2 (application)", command)
        self.matchoutput(out, "Resource: gnr.1 (filesystem)", command)

        command = ["cat", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "'/system/resources/filesystem' = push(create(\"resource/filesystem/host/server1.aqd-unittest.ms.com/gnr.0/config\"))", command)
        self.matchoutput(out, "'/system/resources/application' = push(create(\"resource/application/host/server1.aqd-unittest.ms.com/nydb1/config\"))", command)
        self.matchoutput(out, "'/system/resources/filesystem' = push(create(\"resource/filesystem/host/server1.aqd-unittest.ms.com/gnr.1/config\"))", command)
        self.matchoutput(out, "'/system/resources/application' = push(create(\"resource/application/host/server1.aqd-unittest.ms.com/utdb2/config\"))", command)

    def test_49_cleanup_standalone(self):
        command = ["del_filesystem", "--filesystem=gnr.0",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)
        command = ["del_application", "--application=nydb1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)
        command = ["del_filesystem", "--filesystem=gnr.1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)
        command = ["del_application", "--application=utdb2",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_50_clustered_dbserver(self):
        # We'll just do a single-node cluster for now
        command = ["add_cluster", "--cluster=nydb1",
                   "--campus=ny",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=hacluster", "--personality=vcs-msvcs"]
        self.successtest(command)

        command = ["cluster", "--cluster=nydb1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["add_filesystem", "--filesystem=gnr.0", "--type=ext3",
                   "--mountpoint=/d/d1/nydb1",
                   "--blockdevice=/dev/vx/dg.0/gnr.0",
                   "--nobootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=rw",
                   "--cluster=nydb1"]
        self.successtest(command)

        command = ["add_application", "--application=nydb1", "--eonid=42",
                   "--cluster=nydb1"]
        self.successtest(command)

        command = ["compile", "--cluster=nydb1"]
        self.successtest(command)

        command = ["show_cluster", "--cluster=nydb1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource: nydb1 (application)", command)
        self.matchoutput(out, "Resource: gnr.0 (filesystem)", command)
        self.matchoutput(out, "Member: server1.aqd-unittest.ms.com", command)

        command = ["cat", "--cluster=nydb1"]
        out = self.commandtest(command)
        self.matchoutput(out, "'/system/resources/filesystem' = push(create(\"resource/filesystem/cluster/nydb1/gnr.0/config\"))", command)
        self.matchoutput(out, "'/system/resources/application' = push(create(\"resource/application/cluster/nydb1/nydb1/config\"))", command)

    def test_59_cleanup_cluster(self):
        command = ["del_filesystem", "--filesystem=gnr.0",
                   "--cluster=nydb1"]
        self.successtest(command)
        command = ["del_application", "--application=nydb1", "--cluster=nydb1"]
        self.successtest(command)
        command = ["uncluster", "--hostname=server1.aqd-unittest.ms.com",
                   "--cluster=nydb1"]
        self.successtest(command)
        command = ["del_cluster", "--cluster=nydb1"]
        self.successtest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)
