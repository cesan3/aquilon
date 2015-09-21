#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2015  Contributor
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
"""Module for testing constraints in commands involving vendor."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestVendorConstraints(TestBrokerCommand):

    def testdelvendorwithmodel(self):
        command = "del vendor --vendor hp"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "in use by a model", command)

    def testverifydelvendorwithmodel(self):
        command = ["show_vendor", "--vendor=hp"]
        out = self.commandtest(command)
        self.matchoutput(out, "Vendor: hp", command)

    # TODO: better place for this test
    def testdelxeon2500(self):
        command = "del cpu --cpu xeon_2500 --vendor intel"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Model intel/xeon_2500 is still in use and "
                         "cannot be deleted.", command)

    # TODO: better place for this test
    def testdelxeon2660(self):
        command = "del cpu --cpu unused --vendor utvendor"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Model utvendor/unused is still referenced by "
                         "machine models and cannot be deleted.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestVendorConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
