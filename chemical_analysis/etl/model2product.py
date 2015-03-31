#!/usr/bin/env python
# -*- encoding: utf-8 -*-
''' Search model family in product code (first 6 char of the code) and associate
    correct model to prodcut
'''
# Modules required:
import xmlrpclib, sys, ConfigParser, os

# Start main code *************************************************************
path=os.path.expanduser("~/ETL/minerals/")
cfg_file=path + "openerp.cfg"

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common' % (server, port), allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (server, port), allow_none=True)

model_ids = sock.execute(dbname, uid, pwd, 'product.product.analysis.model', 'search', [])
model_proxy = sock.execute(dbname, uid, pwd, 'product.product.analysis.model', 'read', model_ids)

family_id={}
for line in model_proxy:
    family_id[line['family']] = (line['id'], line['name'])

product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [])  
for product in sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids):
    code = product['default_code'][:6]
    if code in family_id:
       product_update = sock.execute(
           dbname, uid, pwd, 'product.product', 'write', product['id'],{
               'model_id':family_id[code][0],
               'need_analysis': True,
               })
       print "INFO: [%s] %s > Modello [%s]" % (product['default_code'], product['name'].encode('utf-8'), family_id[code][1].encode('utf-8'))

    else:
       product_update = sock.execute(
           dbname, uid, pwd, 'product.product', 'write', product['id'],{
               'model_id': False,
               'need_analysis': False,
               })
       print "ERR:  [%s] %s > Nessun modello per la famiglia: %s!" % (product['default_code'], product['name'].encode('utf-8'), code)
