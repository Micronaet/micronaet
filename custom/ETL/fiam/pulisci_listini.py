#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Erase old pricelist precedently imported (run after particolarita.py for pikle file)
# use: pulisci_listini.py

# Modules required:
import xmlrpclib, csv, ConfigParser
from mic_ETL import *

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

client_list=cPickleParticInput(file_name_pickle)

# Search customers 
item_partner_ids = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('customer', '=', 'True'),('mexal_c','!=','')])
item_partner= sock.execute(dbname, uid, pwd, 'res.partner', 'read', item_partner_ids, [])
for partner in item_partner:
    if len(partner['mexal_c'])==8:
        if partner['mexal_c'] not in client_list:
           # Unlink items, pricelist, version 
           erase_ids= sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'search', [('mexal_id', '=', partner['mexal_c'])])
           if erase_ids: erase_item = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'unlink', erase_ids)
           erase_ids= sock.execute(dbname, uid, pwd, 'product.pricelist.version', 'search', [('mexal_id', '=', partner['mexal_c'])])
           if erase_ids: erase_item = sock.execute(dbname, uid, pwd, 'product.pricelist.version', 'unlink', erase_ids)
           erase_ids= sock.execute(dbname, uid, pwd, 'product.pricelist', 'search', [('mexal_id', '=', partner['mexal_c'])])
           if erase_ids: erase_item = sock.execute(dbname, uid, pwd, 'product.pricelist', 'unlink', erase_ids)
       
