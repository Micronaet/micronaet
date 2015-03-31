#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# TODO LIST:
# Test numero of colums, there are some cases that separator char is present in fields, ex: email@soc1.it; email@soc2.it in email address
# Modules ETL Partner Scuola
# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib, ConfigParser, pdb

# Set up parameters (for connection to Open ERP Database) ********************************************
# DB config read
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
verbose=eval(config.get('import_mode','verbose'))  # for info message

country_italy=106
et1=2 # internal (article)
et2=1 # external (package)
et3=5 # pallet 


sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

i=0
# TODO: import type_cei for best test of italian customer
partner_id=sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('customer', '=', True),
                                                                    ('country', "=", country_italy),])
if partner_id: 
   partner_list=sock.execute(dbname, uid, pwd, 'res.partner', 'read', partner_id)
   for item in partner_list:
       if item['country'] and item['country'][0]== country_italy:
           i+=1  
           if item['pack_label_id'] and item['article_label_id'] and item['pallet_label_id']: # if one of this is not set up  # or item['pallet_label_id']
              print i, "OK", item['ref'], item['name'], item['country'], item['mexal_c'], item['mexal_s']
           else:
              # update label
              try: 
                 partner_mod= sock.execute(dbname, uid, pwd, 'res.partner', 'write', item['id'], {'pack_label_id': et2, 'article_label_id':  et1, 'pallet_label_id': et3,})
              except:
                 pdb.set_trace()
              print i, "UPD", item['ref'], item['name'], item['country'], item['mexal_c'], item['mexal_s']

