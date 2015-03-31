# -*- encoding: utf-8 -*-
# List field and first 5 element of table in argv
import xmlrpclib,ConfigParser,sys

# Set up parameters (for connection to Open ERP Database) ********************************************
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
 
# For final user: Do not modify nothing below this line (Python Code) ********************************
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common')
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object')

tabella='res.partner'

tabella_id = sock.execute(dbname, uid, pwd, tabella, 'search', []) 
tabella_campi=sock.execute(dbname,uid,pwd,tabella,'read',tabella_id)
tot={'partner':0, 'customer':0, 'supplier':0, 'both': 0, 'address': 0, 'address_extra': 0}

for elemento in tabella_campi:
   tot['partner'] += 1
   if elemento['customer']:
      tot['customer'] += 1
   if elemento['supplier']:
      tot['supplier'] += 1
   if elemento['supplier'] and elemento['customer']:
      tot['both'] += 1
   if elemento['address']:
      tot['address'] += len(elemento['address']) 
tot['address_extra'] += tot['address'] - tot['partner']

print "Totale:       \t%s" % (tot['partner'],)
print "Customer:     \t%s" % (tot['customer'],)
print "Supplier:     \t%s" % (tot['supplier'],)
print "C + S:        \t%s" % (tot['both'],)
print "Address:      \t%s" % (tot['address'],)
print "Address extra:\t%s" % (tot['address_extra'],)

