#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Force last price in product supplierinfo
import xmlrpclib, ConfigParser


# Set up parameters (for connection to Open ERP Database) *********************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg'])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')

# -----------------------------------------------------------------------------
#          XMLRPC connection for autentication (UID) and proxy 
# -----------------------------------------------------------------------------
sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common' % (server, port), 
    allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (server, port), 
    allow_none=True)

# -----------------------------------------------------------------------------
#                          Reset situazione is_active
# -----------------------------------------------------------------------------
table = 'pricelist.partnerinfo'
#item_ids = sock.execute(dbname, uid, pwd, table, 'search', [
#    ('is_active', '=', True)])
#sock.execute(dbname, uid, pwd, table, 'write', item_ids, {'is_active': False})    

# -----------------------------------------------------------------------------
#                            Choose max quotation
# -----------------------------------------------------------------------------
cambio = {}
import pdb; pdb.set_trace()
item_ids = sock.execute(dbname, uid, pwd, table, 'search', [])
for item in sock.execute(dbname, uid, pwd, table, 'read', item_ids ('product_id', 'date_quotation')):
    try:
        if item['product_id']
            product_id = item['product_id'][0]
        else:
            continue    
    except:
        continue  
        
    if product_id not in cambio:
        cambio[product_id] = [item['id'], item['date_quotation']]
    else:
        if item['date_quotation'] > cambio[product_id[1]]:
            cambio[item['product_id']] = [item['id'], item['date_quotation']]

# -----------------------------------------------------------------------------
#                                 Force is active
# -----------------------------------------------------------------------------
# Get ID to update:
item_ids = []
for key in cambio:
    item_ids.append(cambio[key][0])
    print "%s;%s" % (item['product_id'], item['date_quotation'])

# Update is_active
#sock.execute(dbname, uid, pwd, table, 'write', item_ids, {'is_active': True})

