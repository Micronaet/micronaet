#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Modules used for ETL - Create User

# Modules required:
import xmlrpclib, sys, csv, ConfigParser

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

# For final user: Do not modify nothing below this line (Python Code) *********
# Functions:
def Prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def GetAdminGroup(dbname, uid, pwd, group_ids):
    # Create username that own record created (set up admin permission)
    search_id_admin = sock.execute(dbname, uid, pwd, 'res.users', 'search', [('login', '=', 'admin')]) # admin exist!
    read_id_admin = sock.execute(dbname, uid, pwd, 'res.users', 'read', search_id_admin[0])
    for gruppo in read_id_admin['groups_id']:
        group_ids.append(gruppo)

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *   > Use the command with this syntax: python ./ETL_contact.py name_file_csv.csv
         *********************
         """
   sys.exit()

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Initialize variables
#country_not_found=[] # list of county not found
group_ids=[]
GetAdminGroup(dbname, uid, pwd,group_ids) # create user Micronaet or get it
lingua='it_IT'
# Open CSV passed file (see arguments) mode: read / binary, delimiation char ";"
FileInput=sys.argv[1]

# CreateCRMcampaign
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':0,'new':0,'upd':0}

try:
    for line in lines:
        if len(line): 
            start=0 
            name= Prepare(line[0])
            signature=Prepare(line[1]).title()
            login=Prepare(line[2])
            password=Prepare(line[3])
   
            # Start of importation:
            counter['tot'] += 1  

            # test if record exists (basing on Ref. as code of Partner)
            item = sock.execute(dbname, uid, pwd, 'res.users', 'search', [('login', '=', login)])

            if item:  # partner already exist
               counter['upd'] += 1  
               try:                   
                  data = {'name': name,                
                          'signature': signature,    
                          'groups_id': [(6,0,group_ids)],
                          'context_lang': lingua,
                         }                  
                  item_mod = sock.execute(dbname, uid, pwd, 'res.users', 'write', item, data) 
               except:
                  print "[ERROR] Modifing data, current record:", data
                  raise 
               print "[INFO]", counter['tot'], "Already exist: ", name
            else:           
               counter['new'] += 1  
               try:   
                  # Create contact
                  data={'name': name,
                        'signature': signature,
                        'password': password,
                        'login': login,  
                        'groups_id': [(6,0,group_ids)],
                        'context_lang': lingua,
                        }
                  ins_id_contact=sock.execute(dbname, uid, pwd, 'res.users', 'create', data)
                  print "[INFO]",counter['tot'], "Insert: ", name
               except:
                  print "*************************************************************"
                  print "[ERROR] Error creating data, current record: ", data
                  print "*************************************************************"
                  raise  # normal text of error

except:
    print '>>> [ERROR] Error importing data!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Total line: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
