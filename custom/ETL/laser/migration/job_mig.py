# -*- encoding: utf-8 -*-
# Migration from DB 1 to DB 2 (partner - address - job - contact + new inherit simple list m2o relationship)
import xmlrpclib, ConfigParser, sys, pdb
from mic_ETL import *

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])

# Connestion Destination
dbname=config.get('dbaccess2','dbname')
user=config.get('dbaccess2','user')
pwd=config.get('dbaccess2','pwd')
server=config.get('dbaccess2','server')
port=config.get('dbaccess2','port')   

try:
    sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common')
    uid = sock.login(dbname,user,pwd)
    sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object')

    jobs=cPickleParticInput('contatti.pkl')

    for item in jobs:
        item_job= sock.execute(dbname, uid, pwd, 'res.partner.job', 'search', [('address_id', '=', item['address_id']),('contact_id', '=', item['contact_id'])])
        if item_job:  
           item_job_mod = sock.execute(dbname, uid, pwd, 'res.partner.job', 'write', item_job, item) 
        else:           
           job_id=sock.execute(dbname, uid, pwd, 'res.partner.job', 'create', item) 
except:
   pdb.set_trace()
   raise

