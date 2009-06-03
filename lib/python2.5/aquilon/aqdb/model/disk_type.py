""" For the various types of disks we use """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr


_ABV = 'disk_type'
_disk_types = ['cciss', 'ide', 'sas', 'sata', 'scsi', 'flash']


class DiskType(Base):
    """ Disk Type: scsi, cciss, sata, etc. """
    __tablename__  = _ABV

    id = Column(Integer, Sequence('%s_seq'%(_ABV)), primary_key=True)
    type = Column(AqStr(32), nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

disk_type = DiskType.__table__
table = DiskType.__table__

disk_type.primary_key.name='%s_pk'%(_ABV)
disk_type.append_constraint(UniqueConstraint('type',name='%s_uk'%(_ABV)))


def populate(sess, *args, **kw):
    if len(sess.query(DiskType).all()) < 1:
        for t in _disk_types:
            dt = DiskType(type = t)
            sess.add(dt)
        try:
            sess.commit()
        except Exception, e:
            sess.rollback()
            raise e

    dt = sess.query(DiskType).first()
    assert(dt)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
