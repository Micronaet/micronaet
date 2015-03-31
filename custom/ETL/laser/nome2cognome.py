# -*- encoding: utf-8 -*-
import xmlrpclib, ConfigParser

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   
 
# For final user: Do not modify nothing below this line (Python Code) ********************************
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common')
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object')

tabella_id = sock.execute(dbname, uid, pwd, 'res.partner.contact', 'search', ["|",('first_name','!=',''),('first_name','!=',False)])
tabella_contatti = sock.execute(dbname, uid, pwd, 'res.partner.contact', 'read', tabella_id) 
i=0
for contatto in tabella_contatti:
    i+=1 
    print i, contatto['name'], "-", contatto['first_name'], 
    try:  
       mod_contatto = sock.execute(dbname, uid, pwd, 'res.partner.contact', 'write', contatto['id'], {'name': contatto['name'] + " " + contatto['first_name'], 'first_name': False, 'fiscal_id_code': contatto['fiscal_id_code']}) # Imposto il corso come convalidato!
       print ">>> Sostituito" 
    except:
       print ">>> ERRORE IN SCRITTURA!", "C.F.", contatto['fiscal_id_code']

