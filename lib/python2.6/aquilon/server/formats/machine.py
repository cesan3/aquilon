# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Machine formatter."""

from aquilon import const
from aquilon.server.formats.formatters import ObjectFormatter, shift
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.model import Machine


class MachineInterfacePair(tuple):
    """Encapsulates a (machine, selected interface) pair"""
    pass


class MachineInterfacePairFormatter(ObjectFormatter):
    def csv_fields(self, item):
        machine = item[0]
        addr = item[1]

        rack = None
        if machine.location.rack:
            rack = machine.location.rack.name
        building = None
        if machine.location.building:
            building = machine.location.building.name
        details = [machine.label, rack, building, machine.model.vendor.name,
                   machine.model.name, machine.serial_no]
        if addr:
            details.extend([addr.logical_name, addr.interface.mac, addr.ip])
        else:
            details.extend([None, None, None])
        return details

ObjectFormatter.handlers[MachineInterfacePair] = MachineInterfacePairFormatter()


class MachineFormatter(ObjectFormatter):
    def format_raw(self, machine, indent=""):
        # TODO: convert this formatter to mako
        details = [indent + "%s: %s" % (machine.model.machine_type.capitalize(),
                                        machine.label)]
        if machine.primary_name:
            details.append(indent + "  Primary Name: "
                           "{0:a}".format(machine.primary_name))
        if machine.cluster:
            details.append(indent + \
                           "  Hosted by {0:c}: {0.name}".format(machine.cluster))

        # FIXME: This is now somewhat redundant
        managers = []
        auxiliaries = []
        for iface in machine.interfaces:
            for addr in iface.all_addresses():
                if addr.ip == machine.primary_ip:
                    continue
                if iface.interface_type == 'management':
                    managers.append((addr.fqdns, addr.ip))
                else:
                    auxiliaries.append((addr.fqdns, addr.ip))

        for mgr in managers:
            details.append(indent + "  Manager: %s [%s]" %
                           (", ".join(mgr[0]), mgr[1]))
        for aux in auxiliaries:
            details.append(indent + "  Auxiliary: %s [%s]" %
                           (", ".join(aux[0]), aux[1]))

        # This is a bit of a hack.  Delegating out to the standard location
        # formatter now spews too much information about chassis.  Maybe
        # that will change when chassis has a corresponding hardware type.
        for location_type in const.location_types:
            if getattr(machine.location, location_type, None) is not None:
                loc = getattr(machine.location, location_type)
                details.append(indent + "  {0:c}: {0.name}".format(loc))
                if location_type == 'rack':
                    details.append(indent + "    Row: %s" %
                                   machine.location.rack.rack_row)
                    details.append(indent + "    Column: %s" %
                                   machine.location.rack.rack_column)
        for slot in machine.chassis_slot:
            details.append(indent + "  {0:c}: {0!s}".format(slot.chassis))
            details.append(indent + "  Slot: %d" % slot.slot_number)
        details.append(indent + "  {0:c}: {0.name} {1:c}: {1.name}".format(
            machine.model.vendor, machine.model))
        details.append(indent + "  Cpu: %s x %d" %
                (machine.cpu, machine.cpu_quantity))
        details.append(indent + "  Memory: %d MB" % machine.memory)
        if machine.serial_no:
            details.append(indent + "  Serial: %s" % machine.serial_no)
        for d in machine.disks:
            extra = d.disk_type
            if d.disk_type == "nas" and d.service_instance:
                extra = extra + " from " + d.service_instance.name
            details.append(indent + "  Disk: %s %d GB %s (%s)"
                    % (d.device_name, d.capacity, d.controller_type,
                       extra))
        for i in machine.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
        if machine.comments:
            details.append(indent + "  Comments: %s" % machine.comments)
        if machine.host:
            template = self.lookup_raw.get_template("host.mako")
            details.append(shift(template.render(record=machine.host,
                                                 formatter=self),
                                 indent=indent + "  ").rstrip())
        return "\n".join(details)

    def csv_tolist(self, machine):
        if machine.interfaces:
            entries = []
            for iface in machine.interfaces:
                for addr in iface.all_addresses():
                    entries.append(MachineInterfacePair((machine, addr)))
            return entries
        else:
            return [MachineInterfacePair((machine, None))]

ObjectFormatter.handlers[Machine] = MachineFormatter()


class SimpleMachineList(list):
    pass


class SimpleMachineListFormatter(ListFormatter):
    def format_raw(self, smlist, indent=""):
        return str("\n".join([indent + machine.label for machine in smlist]))

ObjectFormatter.handlers[SimpleMachineList] = SimpleMachineListFormatter()


class MachineMacList(list):
    """ Holds MAC, machine-name [, hostname] """
    pass


class MachineMacListFormatter(ListFormatter):
    def csv_fields(self, result):
        return result

ObjectFormatter.handlers[MachineMacList] = MachineMacListFormatter()
