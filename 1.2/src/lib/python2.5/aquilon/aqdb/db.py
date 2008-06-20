#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""To be imported by classes and modules requiring aqdb access"""
from __future__ import with_statement

import sys
sys.path.append('../..')

import os
from socket import gethostname
from datetime import datetime

import depends #includes sqlalchemy for us

from sqlalchemy import (MetaData, create_engine, UniqueConstraint, Table,
                        Integer, DateTime, Sequence, String, select,
                        Column as _Column, ForeignKey as _fk , PassiveDefault)

from sqlalchemy.orm import sessionmaker, scoped_session, deferred, relation
from sqlalchemy.sql import insert, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exceptions import SQLError

from aquilon.config import Config

# Something like this will/should be valid when the broker reads in a
# config file first.  The config object is (essentially) a singleton
# that will already be populated.  In this case, no exception will be thrown.
try:
    config = Config()
except Exception, e:
    print >> sys.stderr, "failed to read configuration: %s" % e
    sys.exit(os.EX_CONFIG)

print "using logfile of %s" % config.get("database", "dblogfile")

import logging
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=config.get("database", "dblogfile"),
                    filemode='w')

dsn = config.get("database", "dsn")
if dsn is None:
    raise KeyError("Can't determine DSN, Check config files and env.")
    sys.exit(9)

if dsn.startswith('oracle'):
    import msversion
    msversion.addpkg('cx-Oracle','4.3.3-10.2.0.1-py25','dist')
    import cx_Oracle
    if not os.environ.get('ORACLE_HOME'):
        os.environ['ORACLE_HOME'] = config.get('database', 'vendor_home')
    if not os.environ.get('ORACLE_SID'):
        os.environ['ORACLE_SID'] = config.get('database', 'server')

engine = create_engine(dsn)

try:
    engine.connect()
except Exception,e:
    print e
    print 'DSN ',dsn
    if dsn.startswith('oracle'):
        print 'ENVIRONMENT VARS:'
        print os.environ['ORACLE_HOME']
        print os.environ['ORACLE_SID']
    sys.exit(1)

meta  = MetaData(engine)
#meta.bind.echo = True

Session = scoped_session(sessionmaker(bind=engine,
                                      autoflush=True,
                                      transactional=True))


#AKA 'duck punching'...this decorator will bolt new methods onto a class
def monkeypatch(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator

# for trying out the declarative mapper for Role. The hope is this will
# cut more time off the development cycle since Base includes a constructor
Base = declarative_base(metadata=meta)

@monkeypatch(Base)
def __repr__(self):
    if hasattr(self,'name'):
        return self.__class__.__name__ + ' ' + str(self.name)
    elif hasattr(self,'type'):
        return self.__class__.__name__ + ' ' + str(self.type)
    elif hasattr(self,'service'):
        return self.__class__.__name__ + ' ' + str(self.service.name)
    elif hasattr(self,'system'):
        return self.__class__.__name__ + ' ' + str(self.system.name)
    else:
       return '%s instance '%(self.__class__.__name__)


def get_date_default():
    if dsn.startswith('oracle'):
        return PassiveDefault(text('sysdate'))
    else:
        return datetime.now

def get_date_col():
    return deferred(Column('creation_date', DateTime,
                           default = get_date_default(), nullable = False))

def get_comment_col():
    return deferred(Column('comments', String(255), nullable = True))

def get_id_col(name):
    return Column('id', Integer, Sequence('%s_seq'%(name)),primary_key=True)


def optional_comments(func):
    """ reduce repeated code to handle 'comments' column """
    def comments_decorator(*__args, **__kw):
        ATTR = 'comments'
        if (__kw.has_key(ATTR)):
            setattr(__args[0], ATTR, __kw.pop(ATTR))
        return func(*__args, **__kw)
    return comments_decorator

class aqdbBase(object):
    """ AQDB base class: All ORM classes will extend aqdbBase.

    While the code is a bit trite, it would be silly not to have this class
    such that we can make use of it later when and if needed. All schema modules
    need to import db, so this is the best place for it
    """
    @optional_comments
    def __init__(self,cn,*args,**kw):
        if cn.isspace() or len(cn) < 1 :
            msg='Names must contain some non-whitespace characters'
            raise ArgumentError(msg)
        if isinstance(cn,str):
            self.name = cn.strip().lower()
        else:
            raise ArgumentError('Incorrect name argument %s' % cn)
            return
    def __repr__(self):
        if hasattr(self,'name'):
            return self.__class__.__name__ + ' ' + str(self.name)
        elif hasattr(self,'service'):
            return self.__class__.__name__ + ' ' + str(self.service.name)
        elif hasattr(self,'system'):
            return self.__class__.__name__ + ' ' + str(self.system.name)
        else:
            return '%s instance '%(self.__class__.__name__)
class aqdbType(aqdbBase):
    """To wrap rows in 'type' tables"""
    @optional_comments
    def __init__(self,type,*args,**kw):
        if type.isspace() or len(type) < 1:
            msg='Names must contain some non-whitespace characters'
            raise ArgumentError(msg)
        if isinstance(type,str):
            self.type = type.strip().lower()
        else:
            raise ArgumentError("Incorrect name argument %s" %(type))
            return
    def name(self):
        return str(self.type)
    def __str__(self):
        return str(self.type)
    def __repr__(self):
        return self.__class__.__name__+' ' +str(self.type)


def Column(*args, **kw):
    """ some curry: default column from SA to default as null=False
        unless it's comments, which we hardcode to standardize
    """
    if not kw.has_key('nullable'):
        kw['nullable']=False;
    return _Column(*args, **kw)

#def ForeignKey(*args, **kw):
#    """ more curry: Oracle has 'on delete RESTRICT' by default
#        This removes it in case you need to """
#
#    if kw.has_key('ondelete'):
#        if kw['ondelete'] == 'RESTRICT':
#            kw.pop('ondelete')
#    if kw.has_key('onupdate'):
#        kw.pop('onupdate')
#    return _fk(*args, **kw)

def id_getter(table,key,value):
    """ Get the id of a row given a table name, and the specification of a
    unique attribute. Useful for defaults and type_ids.

    id_getter('archtype','name','aquilon')
    >>> 1
    """
    sel = select([table.c.id],key==value)
    return engine.execute(sel).scalar()

def gen_id_cache(obj_name):
    """ A helper function for bulk creation. When you need to iterate over a
        result set creating either Location objects, or other tables like
        Network or Hardware which have FK's to a location id, this speeds things
        up quite a bit.

        Argument: the object name which wraps the table you're interested in
        Returns: a dictionary who's keys are the object's name, and values
        are the primary key (id) to the table they are in.
    """
    sess=Session()
    cache={}

    for c in sess.query(obj_name).all():
        cache[str(c.name)]=c
        sess.close()
    return cache

def empty(table):
    """
        Returns True if no rows in table, helps in interative schema population
    """
    if  engine.execute(table.count()).fetchone()[0] < 1:
        return True
    else:
        return False

def fill_type_table(table,items):
    """
        Shorthand for filling up simple 'type' tables
    """
    if not isinstance(table,Table):
        raise TypeError('table argument must be type Table')
        return
    if not isinstance(items,list):
        raise TypeError('items argument must be type list')
        return
    i = insert(table)
    for t in items:
        i.execute(type=t)

def mk_type_table(name, meta=meta, *args, **kw):
    """
        Variant on name_id. Can and should reduce them to a single function
        (later)
    """
    return Table(name, meta, \
                Column('id', Integer, Sequence('%s_id_seq'%name),
                       primary_key=True),
                Column('type', String(32)),
                Column('creation_date', DateTime,
                       default=datetime.now),
                Column('comments', String(255), nullable=True),
                UniqueConstraint('type',name='%s_uk'%name), *args, **kw)

def confirm(prompt=None, resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True

    """

    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')

    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print 'please enter y or n.'
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

def get_table_list_from_db():
    """
    return a list of table names from the current
    databases public schema
    """
    sql='select table_name from user_tables'
    execute = engine.execute
    return [name for (name, ) in execute(text(sql))]

def get_seq_list_from_db():
    """return a list of the sequence names from the current
       databases public schema
    """
    sql='select sequence_name from user_sequences'
    execute = engine.execute
    return [name for (name, ) in execute(text(sql))]

def drop_all_tables_and_sequences():
    """ MetaData.drop_all() doesn't play nice with db's that have sequences.
        you're alternative is to call this"""
    if not dsn.startswith('ora'):
        print 'dsn is not oracle, exiting'
        return False
    msg="You've asked to wipe out the %s database. Please confirm."%(dsn)

    if confirm(prompt=msg, resp=False):
        execute = engine.execute
        for table in get_table_list_from_db():
            try:
                execute(text('DROP TABLE %s CASCADE CONSTRAINTS' %(table)))
            except SQLError, e:
                print >> sys.stderr, e

        for seq in get_seq_list_from_db():
            try:
                execute(text('DROP SEQUENCE %s'%(seq)))
            except SQLError, e:
                print >> sys.stderr, e

def clean_fake_data():
    #TODO: add service_inst, service_map, and use Session if only
    # to test session.delete()
    _drop= """
        delete from physical_interface where interface_id in \
            (select id from interface where comments like '%FAKE%');
        delete from interface where comments like '%FAKE%';
        delete from host where comments like '%FAKE';
        delete from machine where comments like '%FAKE%';
        delete from system where comments like '%FAKE';
        delete from rack where id in (select id from location where comments \
            like '%FAKE%');
        delete from chassis where id in (select id from location where \
            comments like '%FAKE%');
        delete from location where comments like '%FAKE%'; """
    engine.execute(_drop)


if __name__ == '__main__':
    print 'your dsn is %s'%dsn

""" Example of a 'mock' engine to output sql as print statments

    buf = StringIO.StringIO()
    def foo(s, p=None):
        print s
    engine=create_engine('sqlite:///:memory:',strategy='mock',executor=foo)
"""