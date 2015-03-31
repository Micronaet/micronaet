#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules ETL Partner Scuola
# use: partner.py file_csv_to_import

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
dbname = 'laser0812' # 0812'
server = '192.168.100.70'
port = '8069'
separator=';'

domain="SI"
prefix=domain + '-' # Letf part of the code (added to the code ID)
actual_category="Scuola"
actual_company="Laser"

#context={'lang':'it_IT','tz':False} #Set up an italian context 

# Create standard list:
partner_titles=("S.p.A.","S.n.C.","S.r.l.","Soc. Coop.","S.a.S.","S.d.f.",)
contact_titles=("Sig.","Sig.ra","Ing.","Geom.","Rag.","Dott.","Dr.","Avv.to","Comm.",) #"Studente","Docente")
region_list=("Valle D'Aosta","Piemonte","Liguria","Lombardia","Veneto","Trentino Alto Adige","Friuli Venezia Giulia","Emilia Romagna","Toscana","Lazio","Umbria","Marche","Abruzzo","Molise","Campania","Basilicata","Puglia","Calabria","Sicilia","Sardegna",)
category_list={"Laser":("Scuola","Servizi alle imprese","Ufficio apprendistato",),"Tipologia":("Cliente","Fornitore",),"Training":("Studente","Docente","Tutor","Stagista","Genitore/Tutore",),}

# For final user: Do not modify nothing below this line (Python Code) *********
# Functions:
def Prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    # N.B. Now files is in utf-8 
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
    cat_id = sock.execute(dbname, uid, pwd, 'res.partner.category', 'search', [('name', '=', name),]) # TODO filter for parent_id
    if len(cat_id): 
       return cat_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'res.partner.category','create',{'name': name,'parent_id': parent_id or False})  

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
                                                                                 'code': region[0:3].upper(), # first 2 char
                                                                                })  
    return 

def CreateDimension(dbname,uid,pwd,name):
    # create Dimension, if not exist and return ID
    dim_id = sock.execute(dbname, uid, pwd, 'res.partner.dimension', 'search', [('name', '=', name),]) # TODO filter for parent_id
    if len(dim_id):
       return dim_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'res.partner.dimension','create',{'name': name,})  

def CreateSector(dbname,uid,pwd,name):
    # create Sector, if not exist and return ID
    sec_id = sock.execute(dbname, uid, pwd, 'res.partner.sector', 'search', [('name', '=', name),]) # TODO filter for parent_id
    if len(sec_id):
       return sec_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'res.partner.sector','create',{'name': name,})  

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
user_id_modify=GetUserMicronaet(dbname, uid, pwd) # create user Micronaet or get it

# Open CSV passed file (see arguments) mode: read / binary, delimiation char ";"
FileInput=sys.argv[1]

# CreateCRMcampaign
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':0,'new':0,'upd':0}
start=0 # put 1 if there are a ID column

# Create standard value for initial start up of DB
CreateAllRegion(dbname,uid,pwd,region_list)          # Create region from start up tupla
CreateAllCategories(dbname,uid,pwd,category_list)    # Create category structure from start up dic
CreateTitle(dbname,uid,pwd,partner_titles,'partner') # Create standard partner title from tupla
CreateTitle(dbname,uid,pwd,contact_titles,'contact') # Create standard contact title from tupla

# get category of actual company parent, actual office child (for this import)
category_id=CreateCategory(dbname,uid,pwd,actual_category,CreateCategory(dbname,uid,pwd,actual_company))
error=''
try:
    for line in lines:
        if len(line): # jump empty lines 
          #if type(line[0]) != type(""):  #first column is mandatory integer (jump description line)
            counter['tot'] += 1 
            error="Importing line" 
            # CSV file data:
            ref = prefix + line[0 + start]         # ID ref with prefix
            name = Prepare(line[1 + start]).title()
            fiscal_id_code = Prepare(line[3 + start]).upper() or ''
            city = Prepare(line[5 + start]).title() or ''
            supplier = Prepare(line[6 + start]).title()=="True"
            customer = Prepare(line[+ start]).title()=="True"
            notif_participant = Prepare(line[8+start]).title=="True"
            comment=Prepare(line[9+start]).capitalize() or ''
            
            # Country?
            error="Searching partner with ref"
            item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('import', '=', ref)])
            if item:  # test if record exists (basing on Ref. as code of Partner)
               counter['upd'] += 1  
               error="Updating partner"
               try:                   
                  data = {'name': name,
                          'domain': domain,  
                          #'vatnumber': piva,
                          #'customer': True,
                          'fiscal_id_code': fiscal_id_code,
                          'comment': comment,
                          #'category_id': [(6,0,[category_id])], # m2m
                         }                  
                  item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data) # update only name
               except:
                  print "[ERROR] Modifing data, current record:", data
                  raise 
               print "[INFO]", counter['tot'], "Already exist: ", ref, name
            else:           
               counter['new'] += 1  
               error="Creating partner"
               # Create Partner
               data={'import': ref,
                     'domain': domain,
                     'name': name,
                     'fiscal_id_code': fiscal_id_code, 
                     'customer': True,
                     'supplier': supplier,
                     'notif_participant': notif_participant,  
                     #'address_id': [(6,0,{'city': city,                                          })] 
                     #'category_id': [(6,0,[category_id])], # m2m
                     'comment': comment, # TODO create list of "province" / "regioni"
                     #'user_id': user_id_modify, 
                    }      
               #'category_id': [(6,0,[category_id[0]])], # m2m                        
               #print data
               create_id=sock.execute(dbname, uid, pwd, 'res.partner', 'create', data) 

               # Creo il partner ?
               #data={'ref': ref,'name': name,'customer': 1,'website': website,'comment': note,'section_id': team_id,'category_id':[(6,0,[categorie['c_if']])],}
               #ins_id_partner = sock.execute(dbname,uid,pwd,'res.partner','create', data)
               # Create address:
               #data={'city': city,'country_id': country_id,'street': street,'zip' : zipcode,'phone': phone,'fax': fax,'email': email,'partner_id': ins_id_partner,'state_id': region_id}
               #ins_id_address=sock.execute(dbname,uid,pwd,'res.partner.address','create',data)
               # Create jobs:
               #data={'address_id':ins_id_address,'contact_id':ins_id_contact,}
               #ins_job_id = sock.execute(dbname, uid, pwd, 'res.partner.job', 'create', data)
               print "[INFO]",counter['tot'], "Insert: ", ref, name
               #except:
               #   print "*************************************************************"
               #   print "[ERROR] ",error,"Data:", data or ""
               #   print "*************************************************************"
               #   raise  # normal text of error

except:
    print '>>> [ERROR] Error importing data!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Total line: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
