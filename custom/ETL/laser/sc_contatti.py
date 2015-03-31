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
from anag_func import * # micronaet standard function 

# Set up parameters (for connection to Open ERP Database) ********************************************
user = 'admin'
pwd = '30mcrt983'
dbname = "laser0812" 
server = '192.168.100.70'
port = '8069'
separator=';'

domain="SC"
prefix=domain + "-" # For enumerate blocks (on every import increment the number!)

context={'lang':'it_IT','tz':False} #Set up an italian context 

# Create standard list:
partner_titles=("S.p.A.","S.n.C.","S.r.l.","Soc. Coop.","S.a.S.","S.d.f.",)
contact_titles=("Sig.","Sig.ra","Ing.","Geom.","Rag.","Dott.","Dr.","Avv.to","Comm.",) #"Studente","Docente")
region_list=("Valle D'Aosta","Piemonte","Liguria","Lombardia","Veneto","Trentino Alto Adige","Friuli Venezia Giulia","Emilia Romagna","Toscana","Lazio","Umbria","Marche","Abruzzo","Molise","Campania","Basilicata","Puglia","Calabria","Sicilia","Sardegna",)
category_list={"Laser":("Scuola","Servizi alle imprese",),"Tipologia":("Cliente","Fornitore",),"Training":("Studente","Docente","Tutor","Stagista","Genitore/Tutore",),}

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
    else:
       return time.strftime("%d/%m/%Y")

def ShortCut(valore=''): 
    # used for code the title (partner or contact), ex.: Sig.ra > SIGRA
    if valore:
       valore = valore.upper()
       valore = valore.replace('.','')
       valore = valore.replace(' ','')
       return valore

def CreateTitle(dbname,uid,pwd,titles,table):
    # Create standard title for partner (procedure batch from tupla, set up from user)
    for title in titles:
        title_id = sock.execute(dbname, uid, pwd, 'res.partner.title', 'search', [('name', '=', title)])
        if not len(title_id):            
           title_id=sock.execute(dbname,uid,pwd, 'res.partner.title', 'create',{'name': title, 
                                                                               'domain': table, 
                                                                               'shortcut': ShortCut(title),
                                                                              })  

def CreateCategory(dbname,uid,pwd,name,parent_id=0):
    # create Category and return ID, if exist return only ID (we suppose that name are in right case)
    if name:
       cat_id = sock.execute(dbname, uid, pwd, 'res.partner.category', 'search', [('name', '=', name),]) # TODO filter for parent_id
       if len(cat_id): 
          return cat_id[0] # take the first
       else:
          return sock.execute(dbname,uid,pwd,'res.partner.category','create',{'name': name,'parent_id': parent_id or False})  
    else:
       return

def CreateAllCategories(dbname, uid, pwd, category_list):
    # Create standard structure of category based on dictionary + tuple for parent-child structure
    for parent in category_list.keys():
        parent_id=CreateCategory(dbname,uid,pwd,parent) # Create parent category with name of keys
        for child in category_list[parent]:   # Loop for child value of keys               
            CreateCategory(dbname,uid,pwd,child,parent_id) # Create child name with parent link ID
    return # nothing, is a procedure!
        
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

def getRegion(dbname,uid,pwd,region):
    # Get region ID of passed name (use "like" operator for Trentino and Emilia)
    region=region.strip()       
    region=region.title()            
    return sock.execute(dbname, uid, pwd, 'res.country.state', 'search', [('name','like',region)]) 

def CreateAllRegion(dbname,uid,pwd,regions):
    # Create region as a res.country.state linked to Italy nation
    country_id = sock.execute(dbname, uid, pwd, 'res.country', 'search', [('name','=',"Italy")]) 
    for region in regions:
        region_id = sock.execute(dbname, uid, pwd, 'res.country.state', 'search', [('name', '=', region),('country_id','=',country_id)])
        if not len(region_id):            
           region_id=sock.execute(dbname,uid,pwd, 'res.country.state', 'create',{'name': region.title(), 
                                                                                 'country_id': country_id[0], 
                                                                                 'code': region[0:2].upper(), # first 2 char
                                                                                })  
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

# Create standard value for initial start up of DB
CreateAllRegion(dbname,uid,pwd,region_list)          # Create region from start up tupla
#CreateAllCategories(dbname,uid,pwd,category_list)    # Create category structure from start up dic
CreateTitle(dbname,uid,pwd,partner_titles,'partner') # Create standard partner title from tupla
CreateTitle(dbname,uid,pwd,contact_titles,'contact') # Create standard contact title from tupla

try:
    for line in lines:
        if len(line): # jump empty lines
          if counter['tot']==-1:  #jump first line (titles)
             counter['tot']=0
          else:
            # Mapping fields, from CVS to program variable
            # CSV file data:
            #id = prefix + Prepare(line[0])  # Import tranche 1, ex. for ref: I1.41 
            course_ids = line[0 + start] # unused
            partner_id = line[1] #unused
            matricola = Prepare(line[2 + start]).upper()
            first_name = Prepare(line[3 + start]).title()
            job_id=Prepare(line[4 + start]) # unused
            country_id = getCountry(dbname,uid,pwd,Prepare(line[5 + start]),country_not_found)
            ref=prefix + Prepare(line[6 + start]).strip()
            email=Prepare(line[7 + start]).lower()
            birthplace=Prepare(line[8 + start]).title() 
            fiscal_id_code=Prepare(line[9 + start]).upper() 
            function_id=Prepare(line[10 + start]).title() # m2o relation (Studente / Insegnante)
            
            name=Prepare(line[12 + start]).title() 
            mobile=Prepare(line[13 + start])             # Check left 0
            birthdate=PrepareDate(line[14 + start])
            
            # Start of importation:
            counter['tot'] += 1  

            # test if record exists (basing on Ref. as code of Partner)
            item = sock.execute(dbname, uid, pwd, 'res.partner.contact', 'search', [('import', '=', ref)])

            if item:  # contact already exist
               counter['upd'] += 1  
               try:                   
                  data = {'name': name,
                          'first_name': first_name,    
                          'matricola':matricola,
                          'birthplace':birthplace,  
                          'domain': domain,    
                          #'country_id': countr_id, 
                         }                  
                  item_mod = sock.execute(dbname, uid, pwd, 'res.partner.contact', 'write', item, data) # update only name
               except:
                  print "[ERROR] Modifing data, current record:", data
                  raise 
               print "[INFO]", counter['tot'], "Already exist: ", ref, name
            else:           
               counter['new'] += 1  
               try:   
                  # Create contact
                  data={'name': name,
                        'first_name': first_name,    
                        'birthdate': birthdate,
                        'birthplace': birthplace,
                        'country_id': country_id,
                        'fiscal_id_code': fiscal_id_code,
                        'mobile': mobile,                          
                        'import': ref, # remember import ID for modify
                        'matricola':matricola,
                        'domain': domain,
                       }
                  ins_id_contact=sock.execute(dbname, uid, pwd, 'res.partner.contact', 'create', data)

                  print "[INFO]",counter['tot'], "Insert: ", ref, name
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

