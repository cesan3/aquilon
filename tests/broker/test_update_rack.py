#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the update rack command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestUpdateRack(TestBrokerCommand):
    # Was row a column 3
    def testupdateut3(self):
        self.noouttest(["update", "rack", "--name", "ut3", "--row", "b"])

    # Was row g column 2
    def testupdateut8(self):
        self.noouttest(["update", "rack", "--name", "ut8", "--column", "8"])

    # Was row g column 3
    def testupdateut9(self):
        self.noouttest(["update", "rack", "--name", "ut9", "--row", "h",
                        "--column", "9", "--fullname", "My Rack",
                        "--comments", "Testing a rack update"])

    def testverifyupdateut9(self):
        command = "show rack --name ut9"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: ut9", command)
        self.matchoutput(out, "Fullname: My Rack", command)
        self.matchoutput(out, "Row: h", command)
        self.matchoutput(out, "Column: 9", command)
        self.matchoutput(out, "Comments: Testing a rack update", command)

    # Was row zz column 99
    def testupdatenp997(self):
        self.noouttest(["update", "rack", "--name", "np997", "--row", "xx",
                        "--column", "77", "--fullname", "My Other Rack",
                        "--comments", "Testing another rack update"])

    def testverifyupdatenp997(self):
        command = "show rack --name np997"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: np997", command)
        self.matchoutput(out, "Fullname: My Other Rack", command)
        self.matchoutput(out, "Row: xx", command)
        self.matchoutput(out, "Column: 77", command)
        self.matchoutput(out, "Comments: Testing another rack update", command)

    # Was row yy column 88
    def testupdatenp998(self):
        self.noouttest(["update", "rack", "--name", "np998", "--row", "vv",
                        "--column", "66"])

    def testfailrow(self):
        command = ["update", "rack", "--name", "np999", "--row", "a-b"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "contained non-alphabet characters", command)

    def testfailcolumn(self):
        command = ["update", "rack", "--name", "np999", "--column", "a"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Expected an integer for column", command)

    def testverifyshowallcsv(self):
        command = "show rack --all --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "rack,ut3,building,ut,b,3", command)
        self.matchoutput(out, "rack,ut8,building,ut,g,8", command)
        self.matchoutput(out, "rack,ut9,building,ut,h,9", command)
        self.matchoutput(out, "rack,np997,building,np,xx,77", command)
        self.matchoutput(out, "rack,np998,building,np,vv,66", command)
        self.matchoutput(out, "rack,np999,building,np,zz,11", command)

    def testverifyut3plenary(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"rack/name" = "ut3";', command)
        self.matchoutput(out, '"rack/row" = "b";', command)
        self.matchoutput(out, '"rack/column" = "3";', command)

    def testverifyut8plenary(self):
        command = "cat --machine ut8s02p1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"rack/name" = "ut8";', command)
        self.matchoutput(out, '"rack/row" = "g";', command)
        self.matchoutput(out, '"rack/column" = "8";', command)

    def testverifyut9plenary(self):
        command = "cat --machine ut9s03p1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"rack/name" = "ut9";', command)
        self.matchoutput(out, '"rack/row" = "h";', command)
        self.matchoutput(out, '"rack/column" = "9";', command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateRack)
    unittest.TextTestRunner(verbosity=2).run(suite)

