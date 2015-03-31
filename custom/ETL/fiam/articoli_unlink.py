#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os
from mx.DateTime import now
from mic_ETL import *
from fiam import *

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
              
pl_item = sock.execute(dbname, uid, pwd, 'product.pricelist', 'search', [('import', '=', True),])                
print pl_item
for listino in pl_item:
    pl_item_item =sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'search', [('price_version_id', '=', listino),])                 
    pl_item_erase=sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'unlink', pl_item_item)                 
    print listino, len(pl_item_item)


#for elemento in pl_item

#try:
# if item_item: # update
#     modify_item = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'write', item_item, item_data)                                    
# else:           
#     new_item_id=sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'create', item_data) 
#except:
#  print "[ERROR] Creating / Modifying item in pricelist", item_data
#  raise 
#except:
#    print '>>> [ERROR] Error importing articles!'
#    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

#print "[INFO]","Articles:", "Total: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
