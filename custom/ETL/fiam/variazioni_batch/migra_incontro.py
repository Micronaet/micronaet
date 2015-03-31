#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Migro l'informazione di contatto (es. Fiera Spoga) dalla lead al partner

# Modules required:
import ConfigParser, xmlrpclib, sys

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

lead_ids = sock.execute(dbname, uid, pwd, 'crm.lead', 'search', [])
read_lead = sock.execute(dbname, uid, pwd, 'crm.lead', 'read', lead_ids, ['type_id','partner_id',])

for lead in read_lead:
    if lead['type_id'] and lead['partner_id'] :
       item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', [lead['partner_id'][0]], {'type_id': lead['type_id'][0],})

#'type_id': fields.many2one('crm.case.resource.type', 'Campaign', ),

