# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del host`."""


import os

from threading import Lock
from twisted.python import log
from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import (hostname_to_host, get_host_dependencies)
from aquilon.server.dbwrappers.service_instance import get_client_service_instances
from aquilon.server.processes import (DSDBRunner, build_index)
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.templates.service import PlenaryServiceInstanceServer
from aquilon.server.templates.base import (compileLock, compileRelease)

delhost_lock = Lock()


class CommandDelHost(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, hostname, user, **arguments):
        # removing the plenary host requires a compile lock, however
        # we want to avoid deadlock by the fact that we're messing
        # with two locks here, so we want to be careful. We grab the
        # plenaryhost early on (in order to get the filenames filled
        # in from the db info before we delete it from the db. We then
        # hold onto those references until we've completed the db
        # cleanup and if all of that is successful, then we delete the
        # plenary file (which doesn't require re-evaluating any stale
        # db information) after we've released the delhost lock.
        delplenary = False

        log.msg("Aquiring lock to attempt to delete %s" % hostname)
        delhost_lock.acquire()
        bindings = [] # Any service bindings that we need to clean up afterwards
        try:
            log.msg("Aquired lock, attempting to delete %s" % hostname)
            # Check dependencies, translate into user-friendly message
            dbhost = hostname_to_host(session, hostname)
            builddir = os.path.join(self.config.get("broker", "builddir"), "domains", dbhost.domain.name, "profiles")
            ph = PlenaryHost(dbhost)
            domain = dbhost.domain.name
            fqdn   = dbhost.fqdn
            deps = get_host_dependencies(session, dbhost)
            if (len(deps) != 0):
                deptext = "\n".join(["  %s"%d for d in deps])
                raise ArgumentError("cannot delete host '%s' due to the following dependencies:\n%s"%(hostname, deptext))

            archetype = dbhost.archetype.name
            dbmachine = dbhost.machine
            ip = dbhost.ip
    
            for binding in dbhost.templates:
                if (binding.cfg_path.svc_inst):
                    bindings.append(binding.cfg_path.svc_inst)
                log.msg("Before deleting host '%s', removing binding '%s'"
                        % (fqdn, binding.cfg_path))
                session.delete(binding)

            session.delete(dbhost)
            session.flush()
            delplenary = True
    
            if archetype != 'aurora':
                try:
                    dsdb_runner = DSDBRunner()
                    dsdb_runner.delete_host_details(ip)
                except ProcessException, e:
                    raise ArgumentError("Could not remove host %s from dsdb: %s" %
                            (hostname, e))

            session.refresh(dbmachine)
        finally:
            log.msg("Released lock from attempt to delete %s" % hostname)
            delhost_lock.release()

        # Only if we got here with no exceptions do we clean the template
        if (delplenary):
            try:
                compileLock()
                ph.remove(builddir, locked=True)
                profiles = self.config.get("broker", "profilesdir")
                plenarydir = self.config.get("broker", "plenarydir")

                # Update any plenary client mappings
                for si in bindings:
                    log.msg("removing plenary from binding for %s"%si.cfg_path)
                    plenary_info = PlenaryServiceInstanceServer(si.service, si)
                    plenary_info.write(plenarydir, locked=True)

                # subsidiary cleanup for hygiene
                # (we don't actually care if these fail, since it doesn't break anything)
                qdir = self.config.get("broker", "quattordir")
                for file in [
                    os.path.join(self.config.get("broker", "depsdir"), domain, fqdn+".dep"),
                    os.path.join(profiles, fqdn+".xml"),
                    os.path.join(qdir, "build", "xml", domain, fqdn+".xml"),
                    os.path.join(qdir, "build", "xml", domain, fqdn+".xml.dep")
                    ]:
                    try:
                        os.remove(file)
                    except:
                        pass
            finally:
                compileRelease()
                
            build_index(self.config, session, profiles)

        return


