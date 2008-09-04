#!/ms/dist/python/PROJ/core/2.5.0/bin/python
"""Classes and Tables relating to network interfaces"""


from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Column, Table, Integer, Sequence, String, Index,
                        Boolean, CheckConstraint, UniqueConstraint, DateTime,
                        ForeignKey, PrimaryKeyConstraint, insert, select)
from sqlalchemy.orm import mapper, relation, deferred

from aquilon.aqdb.column_types.aqmac import AqMac
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.column_types.IPV4  import IPV4
from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.net.network        import Network
from aquilon.aqdb.net.a_name         import AName
from aquilon.aqdb.hw.hardware_entity import HardwareEntity

class Interface(Base):
    __tablename__ = 'interface'

    id             = Column(Integer,
                            Sequence('interface_seq'), primary_key=True)

    name = Column(AqStr(32), nullable = False) #like e0, hme1, etc.

    mac  = Column(AqMac(17), nullable = False)

    ip   = Column(IPV4, nullable = True)

    bootable = Column(Boolean, nullable = False, default = False)


    a_name_id = Column(Integer, ForeignKey(AName.c.id,
                                           name='iface_a_name_fk',
                                           ondelete='CASCADE'),
                       nullable=True) #this is different than
    #the one in hardware_entity: hw_entity's a_name is the "primary" name, where
    #as these are hostname-e0, hostname-e1...It also needs checking on Monday

    interface_type = Column(AqStr(32), nullable = False) #TODO: index

    hardware_entity_id = Column(Integer, ForeignKey(HardwareEntity.c.id,
                                                    name = 'IFACE_HW_ENT_FK',
                                                    ondelete = 'CASCADE'),
                        nullable = False)

    network_id      = Column(Integer, ForeignKey(Network.__table__.c.id,
                                                name = 'iface_net_id_fk'),
                            nullable = True)

    creation_date   = deferred(Column('creation_date',
                                    DateTime, default = datetime.now,
                                    nullable = False))

    comments        = deferred(Column(
                                'comments',String(255)))

    hardware_entity = relation(HardwareEntity, backref = 'interfaces',
                             passive_deletes = True)

    a_name     = relation(AName, uselist = False, passive_deletes=True)

    network    = relation(Network, backref = 'interfaces')

    # We'll need seperate python classes for each subtype if we want to
    # use single table inheritance like this.
    #__mapper_args__ = {'polymorphic_on' : interface_type}

interface = Interface.__table__
interface.primary_key.name = 'interface_pk'

table = interface

interface.append_constraint(UniqueConstraint('mac', name = 'iface_mac_addr_uk'))
interface.append_constraint(UniqueConstraint('ip',  name = 'iface_ip_addr_uk'))
interface.append_constraint(UniqueConstraint('hardware_entity_id', 'name',
                                             name = 'iface_hw_name_uk'))
Index('iface_net_id_idx', interface.c.network_id)
Index('iface_mac_idx', interface.c.mac)
Index('iface_ip_idx', interface.c.ip)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
