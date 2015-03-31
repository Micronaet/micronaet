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

#tabella='product.pricelist.item'
tabella='easylabel.batch.line'
tabella_id = sock.execute(dbname, uid, pwd, tabella, 'search', []) 
tabella_campi=sock.execute(dbname,uid,pwd,tabella,'read',tabella_id)
i=0
if tabella_campi:
    for elemento in tabella_campi:
        if i==0:
            print "***** CAMPI ******************************************"
            print "\n".join(elemento.keys())
            print "******************************************************"
        i+=1
        print "***** N. ",i,":",elemento
        if i==5:
           break
else:
    print "Tabella senza elementi, non possibile rilevare i campi"
