#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import xmlrpclib


# Set up parameters (for connection to Open ERP Database) ********************************************
dbname = "database"
user = "admin"
pwd = "password"
server = "192.168.1.2"
port = 8069


# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common' % (server, port), allow_none = True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (server, port), allow_none = True)

i = 0
item_ids = sorted(sock.execute(dbname, uid, pwd, 'chemical.analysis', 'search', [('code','=',False)]))
for item_id in item_ids:
    i += 1
    code = "AC%05d" % (i)
    sock.execute(dbname, uid, pwd, 'chemical.analysis', 'write', item_id, {'code': code})
    print item_id, code

