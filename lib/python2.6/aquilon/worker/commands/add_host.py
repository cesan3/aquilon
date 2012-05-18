# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Contains the logic for `aq add host`."""


from aquilon.exceptions_ import ArgumentError, ProcessException, AquilonError
from aquilon.aqdb.model import (Host, OperatingSystem, Archetype,
                                HostLifecycle, Machine, Personality,
                                ServiceAddress, HostResource)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.interface import generate_ip, assign_address
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.locks import lock_queue
from aquilon.worker.processes import DSDBRunner


def get_boot_interface(dbmachine):
    dbinterface = None
    # Look up the boot interface
    for iface in dbmachine.interfaces:
        if iface.bootable:
            dbinterface = iface
            # If the boot interface is enslaved in a bonding/bridge setup,
            # then assign the address to the master instead
            while dbinterface.master:
                dbinterface = dbinterface.master
            break
    return dbinterface


class CommandAddHost(BrokerCommand):

    required_parameters = ["hostname", "machine", "archetype"]

    def render(self, session, logger, hostname, machine, archetype, domain,
               sandbox, osname, osversion, buildstatus, personality, comments,
               zebra_interfaces, grn, eon_id, skip_dsdb_check=False,
               **arguments):
        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     compel=True)

        if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
            raise ArgumentError("Adding hosts to {0:l} is not allowed."
                                .format(dbbranch))

        if not buildstatus:
            buildstatus = 'build'
        dbstatus = HostLifecycle.get_unique(session, buildstatus, compel=True)
        dbmachine = Machine.get_unique(session, machine, compel=True)
        oldinfo = DSDBRunner.snapshot_hw(dbmachine)

        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        if not personality:
            if dbarchetype.name == 'aquilon':
                personality = 'inventory'
            else:
                personality = 'generic'
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)

        if dbarchetype.name == 'aquilon':
            # default to os linux/5.0.1-x86_64 for aquilon
            if not osname:
                osname = 'linux'
            if not osversion:
                osversion = '5.0.1-x86_64'
        elif dbarchetype.name == 'aurora':
            if not osname:
                #no solaris yet
                osname = 'linux'
            if not osversion:
                osversion = 'generic'
        elif dbarchetype.name == 'windows':
            if not osname:
                osname = 'windows'
            if not osversion:
                osversion = 'generic'
        else:
            if not osname or not osversion:
                raise ArgumentError("Can not determine a sensible default OS "
                                    "for archetype %s. Please use the "
                                    "--osname and --osversion parameters." %
                                    (dbarchetype.name))

        dbos = OperatingSystem.get_unique(session, name=osname,
                                          version=osversion,
                                          archetype=dbarchetype, compel=True)

        if (dbmachine.model.machine_type == 'aurora_node' and
                dbpersonality.archetype.name != 'aurora'):
            raise ArgumentError("Machines of type aurora_node can only be "
                                "added with archetype aurora.")

        if dbmachine.host:
            raise ArgumentError("{0:c} {0.label} is already allocated to "
                                "{1:l}.".format(dbmachine, dbmachine.host))

        dbhost = Host(machine=dbmachine, branch=dbbranch,
                      sandbox_author=dbauthor, personality=dbpersonality,
                      status=dbstatus, operating_system=dbos, comments=comments)
        session.add(dbhost)

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                               config=self.config)
            dbhost.grns.append(dbgrn)

        if zebra_interfaces:
            # --autoip does not make sense for Zebra (at least not the way it's
            # implemented currently)
            dbinterface = None
        else:
            dbinterface = get_boot_interface(dbmachine)

        # This method is allowed to return None. This can only happen
        # (currently) using add_aurora_host, add_windows_host, or possibly by
        # bypassing the aq client and posting a request directly.
        ip = generate_ip(session, dbinterface, **arguments)

        dbdns_rec, newly_created = grab_address(session, hostname, ip,
                                                allow_restricted_domain=True,
                                                allow_reserved=True,
                                                preclude=True)
        dbmachine.primary_name = dbdns_rec

        if zebra_interfaces:
            if not ip:
                raise ArgumentError("Zebra configuration requires an IP address.")
            dbsrv_addr = self.assign_zebra_address(session, dbmachine, dbdns_rec,
                                                   zebra_interfaces)
        else:
            if ip:
                if not dbinterface:
                    raise ArgumentError("You have specified an IP address for the "
                                        "host, but {0:l} does not have a bootable "
                                        "interface.".format(dbmachine))
                assign_address(dbinterface, ip, dbdns_rec.network)
            dbsrv_addr = None

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbmachine))
        if dbmachine.cluster:
            plenaries.append(Plenary.get_plenary(dbmachine.cluster))
        if dbsrv_addr:
            plenaries.append(Plenary.get_plenary(dbsrv_addr))

        key = plenaries.get_write_key()
        try:
            lock_queue.acquire(key)
            plenaries.write(locked=True)

            # XXX: This (and some of the code above) is horrible.  There
            # should be a generic/configurable hook here that could kick
            # in based on archetype and/or domain.
            dsdb_runner = DSDBRunner(logger=logger)
            if dbhost.archetype.name == 'aurora':
                # For aurora, check that DSDB has a record of the host.
                if not skip_dsdb_check:
                    try:
                        dsdb_runner.show_host(hostname)
                    except ProcessException, e:
                        raise ArgumentError("Could not find host in DSDB: %s" % e)
            elif not dbmachine.primary_ip:
                logger.info("No IP for %s, not adding to DSDB." % dbmachine.fqdn)
            else:
                try:
                    dsdb_runner.update_host(dbmachine, oldinfo)
                except AquilonError, err:
                    raise ArgumentError("Could not add host to DSDB: %s" % err)
        except:
            plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return

    def assign_zebra_address(self, session, dbmachine, dbdns_rec,
                             zebra_interfaces):
        """ Assign a Zebra-managed address to multiple interfaces """

        # Reset the routing configuration
        for iface in dbmachine.interfaces:
            if iface.default_route:
                iface.default_route = False

        # Disable autoflush, since the ServiceAddress object won't be complete
        # until add_resource() is called
        # TODO: In SQLA 0.7.6, we'd be able to use "with session.no_autoflush:"
        saved_autoflush = session.autoflush
        session.autoflush = False

        resholder = HostResource(host=dbmachine.host)
        session.add(resholder)
        dbsrv_addr = ServiceAddress(name="hostname", dns_record=dbdns_rec)
        resholder.resources.append(dbsrv_addr)

        for name in zebra_interfaces.split(","):
            dbinterface = None
            for iface in dbmachine.interfaces:
                if iface.name == name:
                    dbinterface = iface
            if not dbinterface:
                raise ArgumentError("{0} does not have an interface named "
                                    "{1}.".format(dbmachine, name))
            assign_address(dbinterface, dbdns_rec.ip, dbdns_rec.network,
                           label="hostname", resource=dbsrv_addr)

            # Transits should be providers of the default route
            dbinterface.default_route = True

        session.autoflush = saved_autoflush

        return dbsrv_addr
