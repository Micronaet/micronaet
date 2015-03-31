# -*- encoding: utf-8 -*-
# Migration from DB 1 to DB 2 (partner - address - job - contact + new inherit simple list m2o relationship)
import xmlrpclib, ConfigParser, sys, pdb

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])

# Connection Origin
dbname1=config.get('dbaccess1','dbname')
user1=config.get('dbaccess1','user')
pwd1=config.get('dbaccess1','pwd')
server1=config.get('dbaccess1','server')
port1=config.get('dbaccess1','port')   

# Connestion Destination
dbname2=config.get('dbaccess2','dbname')
user2=config.get('dbaccess2','user')
pwd2=config.get('dbaccess2','pwd')
server2=config.get('dbaccess2','server')
port2=config.get('dbaccess2','port')   

# Function:
def GetAdminGroup(sock, dbname, uid, pwd, group_ids):
    # get all admin computer groups
    pdb.set_trace()
    search_id_admin = sock.execute(dbname, uid, pwd, 'res.users', 'search', [('login', '=', 'admin')])
    read_id_admin = sock.execute(dbname, uid, pwd, 'res.users', 'read', search_id_admin[0])
    for gruppo in read_id_admin['groups_id']:
        group_ids.append(gruppo)

# ad hoc procedure:
def PrepareDictionary(item, group_ids):
    pdb.set_trace()
    del item['id']
    del item['address_id'] # def false
    del item['company_id']
    del item['company_ids']
    #menu_id=1  # rimane 1 come nel vecchio
    #context_tz=False 
    #password
    item['context_lang']='it_IT'
    #name
    #groups_id #m2m << prendere quelli dell'administrator
    item['groups_id']= [(6,0,group_ids)]
    #action_id=False
    #company_id 1 # def
    #company_ids=1 # def
    #active=True # def
    #email
    #signature
    #date
    #login
    #menu_tips # def 
    #id=
    #user_email=False
    #view="extended"
    
try:
    sock1 = xmlrpclib.ServerProxy('http://' + server1 + ':' + port1 + '/xmlrpc/common')
    uid1 = sock1.login(dbname1,user1,pwd1)
    sock1 = xmlrpclib.ServerProxy('http://' + server1 + ':' + port1 + '/xmlrpc/object', allow_none=True)

    sock2 = xmlrpclib.ServerProxy('http://' + server2 + ':' + port2 + '/xmlrpc/common')
    uid2 = sock2.login(dbname2,user2,pwd2)
    sock2 = xmlrpclib.ServerProxy('http://' + server2 + ':' + port2 + '/xmlrpc/object', allow_none=True)

    table='res.users'
    
    group_ids=[]
    GetAdminGroup(sock2, dbname2, uid2, pwd2, group_ids)
    
    recordO_ids = sock1.execute(dbname1, uid1, pwd1, table, 'search', [('login','!=','admin')]) 
    if recordO_ids:
       itemO_ids=sock1.execute(dbname1, uid1, pwd1, table,'read',recordO_ids)
       for itemO in itemO_ids:
           PrepareDictionary(itemO, group_ids) 
           recordD_ids = sock2.execute(dbname2, uid2, pwd2, table, 'search', [('login','=',itemO['login'])])
           if recordD_ids: # Update
              modD_ids=sock2.execute(dbname2, uid2, pwd2, table, 'write', recordD_ids[0], itemO) # no [0] is only one
              print "[INFO] Modify", table, itemO['login']
           else: # New
              insD_ids=sock2.execute(dbname2, uid2, pwd2, table, 'create', itemO)
              print "[INFO] Created", table, itemO['login']
except:
   pdb.set_trace()
   raise

