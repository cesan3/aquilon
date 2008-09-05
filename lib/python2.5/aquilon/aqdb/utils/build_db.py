#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" The way to populate an aqdb instance """

import re
import sys
import os
import optparse

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.db_factory    import db_factory, Base, debug
from aquilon.aqdb.utils.shutils import ipshell
from aquilon.aqdb.utils         import table_admin as ta, constraints as cnst

pkgs         = {}

pkgs['auth'] = ['role', 'realm', 'user_principal']

pkgs['loc']  = ['location', 'company', 'hub', 'continent', 'campus', 'country',
                'city', 'building', 'rack', 'desk', 'location_search_list', 
                'search_list_item'] #deleted chassis

pkgs['net']  = ['dns_domain', 'network']

pkgs['cfg']  = ['archetype', 'tld', 'cfg_path']

pkgs['hw']   = ['status', 'vendor', 'model', 'hardware_entity', 'cpu',
                'disk_type', 'machine', 'disk', 'tor_switch_hw', 'chassis_hw', 
                'interface', 'switch_port', 'machine_specs', 'chassis_slot'] 
                #terminal_server, model_subtype

pkgs['sy']   = ['system', 'quattor_server', 'domain', 'host', 'build_item',
                'chassis', 'tor_switch']
               #'system_list', 'system_list_item']

pkgs['svc']  = ['service', 'service_instance', 'service_instance_server',
                'service_map', 'service_list_item']

order = ['auth', 'loc', 'net', 'cfg', 'hw', 'sy', 'svc' ]

def importName(modulename, name):
    """ Import a named object from a module in the context of this function.
    """
    try:
        module = __import__(modulename, globals(), locals(), [name])
    except ImportError:
        return None
    return getattr(module, name)

def main(*args, **kw):
    usage = """ usage: %prog [options]
    rebuilds the aquilon data store (aqdb) from scratch """

    parser = optparse.OptionParser(usage=usage)

    parser.add_option('-v', '--verbose',
                      action  = 'store_true',
                      dest    = 'verbose',
                      help    = 'makes metadata bind.echo = True')

    parser.add_option('-d', '--debug',
                      action  = 'store_true',
                      dest    = 'debug',
                      help    = 'write debug info on stdout')

    parser.add_option('-m', '--mock',
                      action  = 'store_true',
                      dest    = 'mock',
                      help    = 'if selected, creates DDL sql files')

    parser.add_option('-n', '--no',
                      action  = 'store_false',
                      dest    = 'delete_db', \
                      help    = 'do not empty DB',
                      default = True)

    parser.add_option('-p', '--populate',
                      action  = 'store_true',
                      dest    = 'populate',
                      help    = 'run functions to prepopulate data',
                      default = False)

    (opts, args) = parser.parse_args()

    if opts.mock:
        db = db_factory('mock')
    else:
        db = db_factory()

    Base.metadata.bind = db.engine

    if opts.verbose:
        db.meta.bind.echo = True
    else:
        db.meta.bind.echo = False

    assert(db)

    if opts.delete_db == True and db.dsn.startswith('oracle'):
        ta.drop_all_tables_and_sequences(db,opts.delete_db)

    #fill this with module objects if we're populating 
    mods_to_populate = []
    
    for p in order:
        for module_name in pkgs[p]:
            pkg_name = 'aquilon.aqdb.%s'%(p)

            try:
                mod = importName(pkg_name,module_name)
            except ImportError, e:
                print >> sys.stderr, 'Failed to import %s\n' % (module_name, e)
                sys.exit(1)

            if hasattr(mod,'table'):
                debug('\tcreating %s'%(mod.table.name))
                #not in use yet
                #    sqlfile = os.path.splitext(
                #    os.path.basename(mod.__file__))[0] + '.sql'
                #try:
                #    mod.table.create(checkfirst=True)
                #except Exception,e:
                #    sys.stderr.write(str(e))
                #    print e, "\n"

            if hasattr(mod,'populate'):
                mods_to_populate.append(mod) 

    Base.metadata.create_all(checkfirst=True)

    #TODO: if opts.mock: renamer dumps a DDL/SQL file
    if db.dsn.startswith('oracle'):
        debug('renaming constraints...')
        cnst.rename_non_null_check_constraints(db)

    if opts.mock:
        try:
            print db.buf.getvalue()
        except Exception, e:
            if opts.debug:
                ipshell()
            print e
            sys.exit(2)
    elif opts.populate:
        for mod in mods_to_populate:
            debug('populating %s'%(mod.table.name))
            try:
                mod.populate(db)
            except Exception, e:
                sys.stderr.write(str(e))
                print e, "\n"
    else:
        pass

if __name__ == '__main__':
    main(sys.argv)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
"""
import aquilon.aqdb.auth
import aquilon.aqdb.loc
import aquilon.aqdb.hw
import aquilon.aqdb.loc
import aquilon.aqdb.cfg
import aquilon.aqdb.sy
import aquilon.aqdb.svc

pkgs['auth'] = aquilon.aqdb.auth.__all__
pkgs['loc']  = aquilon.aqdb.loc.__all__
pkgs['net']  = ['dns_domain', 'network']
pkgs['cfg']  = aquilon.aqdb.cfg.__all__
pkgs['hw']   = aquilon.aqdb.hw.__all__
pkgs['sy']   = aquilon.aqdb.sy.__all__
pkgs['svc']  = aquilon.aqdb.svc.__all__
"""
