#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Cerco gli ID etichetta
# Pack:
pack_label_id = sock.execute(dbname, uid, pwd, 'easylabel.label', 'search', [('name','=','Italia: Esterna'),('type','=','package')])[0]
# Article:
article_label_id = sock.execute(dbname, uid, pwd, 'easylabel.label', 'search', [('name','=','Italia: Interna'),('type','=','article')])[0]
# Pallet:
pallet_label_id = sock.execute(dbname, uid, pwd, 'easylabel.label', 'search', [('name','=','Italia: bancale'),('type','=','pallet')])[0]

# Cerco i partner italia con le etichette mancanti:
# Pack:
item_empty = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('pack_label_id','=',False),('type_cei','=','i'),]) 
item_mod= sock.execute(dbname, uid, pwd, 'res.partner', 'write', item_empty, {'pack_label_id': pack_label_id,})
# Article:
item_empty = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('article_label_id','=',False),('type_cei','=','i'),]) 
item_mod= sock.execute(dbname, uid, pwd, 'res.partner', 'write', item_empty, {'article_label_id': article_label_id,})
# Pallet:
item_empty = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('pallet_label_id','=',False),('type_cei','=','i'),]) 
item_mod= sock.execute(dbname, uid, pwd, 'res.partner', 'write', item_empty, {'pallet_label_id': pallet_label_id,})
