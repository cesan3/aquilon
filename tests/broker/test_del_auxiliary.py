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
"""Module for testing the del auxiliary command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelAuxiliary(TestBrokerCommand):

    def testdelunittest00e1(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[3])
        command = "del_interface_address --machine ut3c1n3 " \
                  "--fqdn unittest00-e1.one-nyp.ms.com --interface eth1"
        self.statustest(command.split(" "))
        self.dsdb_verify()

    def testverifydelunittest00e1(self):
        command = "show address --fqdn unittest00-e1.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelAuxiliary)
    unittest.TextTestRunner(verbosity=2).run(suite)
