#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Enum column type for network table """

import sqlalchemy.types as types
from exceptions import TypeError

_NETWORK_TYPES = ['transit', 'vip', 'management', 'unknown', 'grid_domain',
                  'legacy', 'stretch']

class NetworkTypeError(TypeError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "Illegal NetworkType '%s'" % self.value

class NetworkType(types.TypeDecorator):
    """a type that decorates String, and serves as an enum-like value check
       for the network table"""

    impl = types.String

    def process_bind_param(self, value, engine):
        value = value.strip().lower()
        if value in _NETWORK_TYPES:
            return value
        else:
            raise NetworkTypeError(value)

    def process_result_value(self, value, engine):
        return value

    def copy(self):
        return NetworkType(self.impl.length)