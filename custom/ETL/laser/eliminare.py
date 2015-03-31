# -*- encoding: utf-8 -*-
import xmlrpclib,ConfigParser,sys

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

tabella='training.seance.plan'
tabella_ids = sock.execute(dbname, uid, pwd, tabella, 'search', []) 
tabella_esito = sock.execute(dbname, uid, pwd, tabella, 'unlink', tabella_ids) 
print tabella, "record eliminati!"
