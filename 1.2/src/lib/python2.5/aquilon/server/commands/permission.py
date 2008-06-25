#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq permission`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.user_principal import (
        get_or_create_user_principal)
from aquilon.server.dbwrappers.role import get_role


class CommandPermission(BrokerCommand):

    required_parameters = ["principal", "role"]

    @add_transaction
    @az_check
    def render(self, session, principal, role, createuser, createrealm,
            **arguments):
        dbrole = get_role(session, role)
        dbuser = get_or_create_user_principal(session, principal, 
                createuser, createrealm)
        dbuser.role = dbrole
        session.save_or_update(dbuser)
        return


#if __name__=='__main__':