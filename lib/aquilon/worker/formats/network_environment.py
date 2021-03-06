# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2017  Contributor
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
"""Network environment formatter."""

from aquilon.aqdb.model import NetworkEnvironment
from aquilon.worker.formats.formatters import ObjectFormatter


class NetworkEnvironmentFormatter(ObjectFormatter):
    def format_raw(self, netenv, indent="", embedded=True,
                   indirect_attrs=True):
        details = [indent + "{0:c}: {0.name}".format(netenv)]
        details.append(self.redirect_raw(netenv.dns_environment, indent + "  "))
        if netenv.location:
            details.append(self.redirect_raw(netenv.location, indent + "  "))
        if netenv.comments:
            details.append(indent + "  Comments: %s" % netenv.comments)
        return "\n".join(details)

    def fill_proto(self, netenv, skeleton, embedded=True, indirect_attrs=True):
        skeleton.name = netenv.name
        self.redirect_proto(netenv.dns_environment, skeleton.dns_environment)
        if netenv.location is not None:
            self.redirect_proto(netenv.location, skeleton.location)


ObjectFormatter.handlers[NetworkEnvironment] = NetworkEnvironmentFormatter()
