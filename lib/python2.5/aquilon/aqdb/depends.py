#!/ms/dist/python/PROJ/core/2.5.0/bin/python
import sys
import msversion

msversion.addpkg('sqlalchemy', '0.4.7-1', 'dist')
#msversion.addpkg('sqlalchemy', '0.5beta', 'dev')

msversion.addpkg('cx_Oracle','4.4-10.2.0.1','dist')
msversion.addpkg('ipython','0.8.2','dist')

#if not sys.modules.has_key('migrate.changeset'):
#    msversion.addpkg('sqlalchemy-migrate', '0.4.4', 'dev')