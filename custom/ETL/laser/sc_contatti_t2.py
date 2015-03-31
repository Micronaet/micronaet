#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules used for ETL customers/suppliers
# use: contact.py file_csv_to_import

# Modules required:
import xmlrpclib
import csv
import sys
import time
import string
from mx.DateTime import now


# Set up parameters (for connection to Open ERP Database) ********************************************
user = 'admin'
pwd = '30mcrt983'
dbname = "training1412"
#dbname='laserbs60' 
server = '192.168.100.70'
#server='172.25.1.202'
port = '8069'
separator=';'

domain="SC"
prefix=domain + ".2-" # For enumerate blocks (on every import increment the number!)

Current_Office="C.F.P."

context={'lang':'it_IT','tz':False} #Set up an italian context 

# For final user: Do not modify nothing below this line (Python Code) *********
# Functions:
def Prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def PrepareDate(valore):
    if valore: # TODO test correct date format
       return valore
    #else:
    #   return time.strftime("%d/%m/%Y")

def GetUserMicronaet(dbname, uid, pwd):
    # Create username that own record created (set up admin permission)
    # User: Micronaet
    search_id_admin = sock.execute(dbname, uid, pwd, 'res.users', 'search', [('login', '=', 'admin')])
    read_id_admin = sock.execute(dbname, uid, pwd, 'res.users', 'read', search_id_admin[0])

    search_id = sock.execute(dbname, uid, pwd, 'res.users', 'search', [('name', '=', 'Micronaet')])
    if len(search_id): 
       user_id=search_id[0]
    else:
       user_id=sock.execute(dbname,uid,pwd,'res.users','create',{'name': 'Micronaet','login': 'Micronaet', 'groups_id': read_id_admin['groups_id'], 'password': pwd}) # Create user like admin (groups and pwd)
    return user_id

def CreateOffice(dbname,uid,pwd,name):
    # create Office
    if name:
       off_id = sock.execute(dbname, uid, pwd, 'base.laser.office', 'search', [('name', '=', name),])
       if len(off_id): 
          return off_id[0] # take the first
       else:
          return sock.execute(dbname,uid,pwd,'base.laser.office','create',{'name': name,})   
    else:
       return 

def getCountry(dbname,uid,pwd,name,not_found=[]):
    # Search nation, return integer of code       
    if name:
       name=name.strip()
       name=name.title() 
       naz_id = sock.execute(dbname,uid,pwd,"res.country","search",[("name","=",name)])
       if naz_id:
          return naz_id[0]
       else:
          if name not in not_found:
             not_found.append(name)
          return # nothing (not exist)
    else:
       return # nothing (not found)

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
country_not_found=[] # list of county not found
user_id_modify=GetUserMicronaet(dbname, uid, pwd) # create user Micronaet or get it

# Open CSV passed file (see arguments) mode: read / binary, delimiation char ";"
FileInput=sys.argv[1]

lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-1,'new':0,'upd':0}
start=0 # put 1 if there are a ID column

try:
    for line in lines:
        if len(line): # jump empty lines
          if counter['tot']==-1:  #jump first line (titles)
             counter['tot']=0
          else:
            # Mapping fields, from CVS to program variable
            # CSV input fileds:
            ref= prefix + Prepare(line[0])
            classe=Prepare(line[1 + start]).title()
            progr=Prepare(line[2 + start])
            last_name=Prepare(line[3 + start]).title()            
            first_name = Prepare(line[4 + start]).title()
            classcode=Prepare(line[5 + start]).title()         
            fiscal_id_code=Prepare(line[6 + start]).upper() 
            birthplace=Prepare(line[7 + start]).title() 
            birthdate=PrepareDate(line[8 + start])
            city=Prepare(line[9 + start]).title()
            street=Prepare(line[10 + start]).title() 
            zipcode=Prepare(line[11 + start])
            phone=Prepare(line[12 + start])
            # Calculated fields: 
            office_id=CreateOffice(dbname,uid,pwd,Current_Office) # get ID of office
            comment="Classe: %s [ %s ] \n Num. reg. %s " % (classe, progr, classcode)

            #country_id = getCountry(dbname,uid,pwd,Prepare(line[5 + start]),country_not_found)
            
            # Start of importation:
            counter['tot'] += 1  

            # test if record exists (basing on Ref. as code of Partner)
            item = sock.execute(dbname, uid, pwd, 'res.partner.contact', 'search', [('import', '=', ref)])

            if item:  # contact already exist
               counter['upd'] += 1  
               try:                   
                  data = {'name': last_name,
                          'first_name': first_name,    
                          #'office_id': office_id, 
                          'domain': domain,
                          #'mobile': phone, 
                         }                  
                  item_mod = sock.execute(dbname, uid, pwd, 'res.partner.contact', 'write', item, data) # update only name
               except:
                  print "[ERROR] Modifing data, current record:", data
                  raise 
               print "[INFO]", counter['tot'], "Already exist: ", ref, first_name, last_name
            else:           
               counter['new'] += 1  
               try:   
                  # Create contact
                  data={'name': last_name,
                        'first_name': first_name,    
                        'city': city,
                        'street': street,      
                        'birthdate': birthdate,
                        'birthplace': birthplace,
                        #'country_id': country_id,
                        'fiscal_id_code': fiscal_id_code,
                        'mobile': phone,   # non correct but is on partner form                       
                        'import': ref,    # remember import ID for modify
                        'domain': domain,
                        'comment':comment,
                        'zip': zipcode,   
                        'office_id': office_id, 
                       }
                  ins_id_contact=sock.execute(dbname, uid, pwd, 'res.partner.contact', 'create', data)

                  print "[INFO]",counter['tot'], "Insert: ", ref, first_name, last_name
               except:
                  print "*************************************************************"
                  print "[ERROR] Error creating data, current record: ", data
                  print "*************************************************************"
                  raise  # normal text of error

except:
    print '>>> [ERROR] Error importing data!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Total line: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
print country_not_found

