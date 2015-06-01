# -*- encoding: utf-8 -*-
# List field and first 5 element of table in argv
import xmlrpclib,ConfigParser,sys, os

# Set up parameters (for connection to Open ERP Database) ********************************************
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/ETL/Minerals/openerp.cfg')]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
 
# For final user: Do not modify nothing below this line (Python Code) ********************************
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common')
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object')

carboni=('04002001',
        '04005001',
        '04005004',
        '04005101',
        '04005102',
        '04005103',
        '04005104',
        '04005301',
        '04005302',
        '04005303',
        '04005304',
        '04005501',
        '04005502',
        '04005503',
        '04005504',
        '04009601',
        '04009602',
        '04009603',
        '04009604',
        '04009605',
        '04009606',
        '04009607',
        '04009608',
        '04000801',
        '04000804',
        '04000702',
        '04000706',
        '04005103',
        '04005002',
        '04005303',
        )
tabella_id = sock.execute(dbname, uid, pwd, 'product.product', 'search', []) 
tabella_reset=sock.execute(dbname,uid,pwd,'product.product','write',tabella_id, {'is_coal': False, 'combine_name':False})

#for item in carboni:
tabella_id = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('default_code', 'in', carboni)]) 
tabella_set = sock.execute(dbname,uid,pwd,'product.product','write',tabella_id, {'is_coal': True, 'combine_name':''})

