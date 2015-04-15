# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq show service`."""

from sqlalchemy.orm import joinedload, subqueryload, undefer, contains_eager

from aquilon.aqdb.model import Service, ServiceInstance
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostname_to_host


class CommandShowService(BrokerCommand):

    def render(self, session, service, instance, server, client, **arguments):
        if service:
            dbservice = Service.get_unique(session, service, compel=True)
            if not client and not server and not instance:
                return dbservice

        q = session.query(ServiceInstance)
        if service:
            q = q.filter_by(service=dbservice)
        if instance:
            q = q.filter_by(name=instance)
        q = q.join(Service)
        q = q.options(contains_eager('service'))

        if server:
            dbserver = hostname_to_host(session, server)
            q = q.join(ServiceInstance.servers, aliased=True)
            q = q.filter_by(host=dbserver)
            q = q.reset_joinpoint()
        elif client:
            dbclient = hostname_to_host(session, client)
            q = q.filter(ServiceInstance.clients.contains(dbclient))

        q = q.options(undefer('_client_count'),
                      subqueryload('servers'),
                      joinedload('servers.host'),
                      joinedload('servers.host.hardware_entity'),
                      subqueryload('service_map'),
                      joinedload('service_map.location'),
                      subqueryload('personality_service_map'),
                      joinedload('personality_service_map.location'))
        q = q.order_by(Service.name, ServiceInstance.name)
        return q.all()
