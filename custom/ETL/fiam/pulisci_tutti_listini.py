#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Erase old pricelist precedently imported (run after particolarita.py for pikle file)
# use: pulisci_listini.py

# Modules required:
import xmlrpclib, ConfigParser

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
file_name_pickle=config.get('dbaccess','file_name_pickle') # Pickle file name

header_lines=0 # non header on CSV file

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Search customers 
try:
    erase_ids= sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'search', [])
    if erase_ids: erase_item = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'unlink', erase_ids)
    erase_ids= sock.execute(dbname, uid, pwd, 'product.pricelist.version', 'search', [])
    if erase_ids: erase_item = sock.execute(dbname, uid, pwd, 'product.pricelist.version', 'unlink', erase_ids)
    erase_ids= sock.execute(dbname, uid, pwd, 'product.pricelist', 'search', [('id','>','10')])
    if erase_ids: erase_item = sock.execute(dbname, uid, pwd, 'product.pricelist', 'unlink', erase_ids)
except:
    raise
