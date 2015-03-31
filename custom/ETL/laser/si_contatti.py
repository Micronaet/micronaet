#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules used for ETL customers/suppliers Laser - Servizi alla societa - Partner
# use: ETL.py file_csv_to_import

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
dbname = 'training1412'
#dbname= 'laserbs60'
server = '192.168.100.70'
#server= '172.25.1.202'
port = '8069'
separator=';'

domain="SI"
prefix=domain + "-1-" # For enumerate blocks (on every import increment the number!)
Current_Office="Servizi alle imprese"

#context={'lang':'it_IT','tz':False} #Set up an italian context 

# Create standard list:
#partner_titles=("S.p.A.","S.n.C.","S.r.l.","Soc. Coop.","S.a.S.","S.d.f.",)
#contact_titles=("Sig.","Sig.ra","Ing.","Geom.","Rag.","Dott.","Dr.","Avv.to","Comm.",) #"Studente","Docente")
#region_list=("Valle D'Aosta","Piemonte","Liguria","Lombardia","Veneto","Trentino Alto Adige","Friuli Venezia Giulia","Emilia Romagna","Toscana","Lazio","Umbria","Marche","Abruzzo","Molise","Campania","Basilicata","Puglia","Calabria","Sicilia","Sardegna",)
#category_list={"Laser":("Scuola","Servizi alle imprese",),"Tipologia":("Cliente","Fornitore",),"Training":("Studente","Docente","Tutor","Stagista","Genitore/Tutore",),}
#office_list=("C.F.P.","Servizi alle imprese",r"Ufficio doti / Apprendistato",)

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

def CreateOfficeList(dbname, uid, pwd, office_list):
    # Create standard structure of category based on dictionary + tuple for parent-child structure
    for office in office_list:
        CreateOffice(dbname,uid,pwd,office) # Create or get ID
    return # nothing is a sub

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
                                                                                 'code': region[0:2].upper(), # first 2 char
                                                                                })  
    return 

# Secondary anagrafics:
def CreateSchoolSheet(dbname,uid,pwd,name):
    # Create school title and return ID if not exist
    if name:
       sch_id = sock.execute(dbname, uid, pwd, 'res.partner.schoolsheet', 'search', [('name', '=', name),])
       if len(sch_id): 
          return sch_id[0] # take the first
       else:
          return sock.execute(dbname,uid,pwd,'res.partner.schoolsheet','create',{'name': name, 'note':''})  
    else:
       return

def CreateProfessionalPosition(dbname,uid,pwd,name): # TODO
    # Create Professional Posizione and return ID if not exist
    if name:
       sch_id = sock.execute(dbname, uid, pwd, 'res.partner.profposition', 'search', [('name', '=', name),])
       if len(sch_id): 
          return sch_id[0] # take the first
       else:
          return sock.execute(dbname,uid,pwd,'res.partner.profposition','create',{'name': name, 'note':''})  
    else:
       return 

def CreateCurrentProfessionStatus(dbname,uid,pwd,name):
    # Create Current profession status (if not exist)
    if name:
       sch_id = sock.execute(dbname, uid, pwd, 'res.partner.profstatus', 'search', [('name', '=', name),])
       if len(sch_id): 
          return sch_id[0] # take the first
       else:
          return sock.execute(dbname,uid,pwd,'res.partner.profstatus','create',{'name': name, 'note':''})  
    else:
       return 

def CreateCurrentProfession(dbname,uid,pwd,name):
    # Create Current profession (if not exist)
    if name:
       sch_id = sock.execute(dbname, uid, pwd, 'res.partner.currentprof', 'search', [('name', '=', name),])
       if len(sch_id): 
          return sch_id[0] # take the first
       else:
          return sock.execute(dbname,uid,pwd,'res.partner.currentprof','create',{'name': name, 'note':''})  
    else:
       return 

def getGender(dbname,uid,pwd,name): 
    # Get not create gender
    if name=="Maschio":
       return "male"
    elif name=="Femmina":
       return "female"
    else:
       return

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

# CreateCRMcampaign
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':0,'new':0,'upd':0}
start=1 # put 1 if there are a ID column

# Create standard value for initial start up of DB
#CreateAllRegion(dbname,uid,pwd,region_list)          # Create region from start up tupla
#CreateOfficeList(dbname,uid,pwd,office_list)         # Create list of Laser Office
office_id=CreateOffice(dbname,uid,pwd,Current_Office) # get ID of office

#CreateAllCategories(dbname,uid,pwd,category_list)    # Create category structure from start up dic
#CreateTitle(dbname,uid,pwd,partner_titles,'partner') # Create standard partner title from tupla
#CreateTitle(dbname,uid,pwd,contact_titles,'contact') # Create standard contact title from tupla

try:
    for line in lines:
        if len(line): # jump empty lines NO TITLE LINE!
            # Mapping fields, from CVS to program variable
            # CSV file data:
            #ref = "I" + trance + "." + Prepare(line[0])  # Import tranche 1, ex. for ref: I1.41 
            ref=prefix + Prepare(line[0])
            project_id = line[0 + start]
            edition_id = line[1 + start]
            name=Prepare(line[2 + start]).title()
            surname=Prepare(line[3 + start]).title()
            sex=Prepare(line[4 + start]).title()       # M20 static selection (Femmina, Maschio)
            birthdate=PrepareDate(line[5 + start])
            birthplace=Prepare(line[6 + start]).title() 
            birthprov=Prepare(line[7 + start]).upper() 
            fiscalcode=Prepare(line[8 + start]).upper() 
            studysheet=Prepare(line[9 + start]).title() # m2o relation 
            disadvantage=Prepare(line[10 + start][0]).upper()=="S"  # Evaluate boolean  (S / N)#####################
            resident_address=Prepare(line[11 + start]).title()
            resident_address_number=Prepare(line[12 + start]).upper()
            resident_city=Prepare(line[13 + start]).title()
            resident_zipcode=Prepare(line[14 + start]) # Check left 0
            resident_prov=Prepare(line[15 + start]).upper()
            resident_phone=Prepare(line[16 + start]) # Check left 0
            mobile=Prepare(line[17 + start]) # Check left 0
            home_address=Prepare(line[18 + start]).title()
            home_address_number=Prepare(line[19 + start]).upper()
            home_city=Prepare(line[20 + start]).title()
            home_zipcode=Prepare(line[21 + start]) # Check left 0
            home_prov=Prepare(line[22 + start]).upper()
            home_phone=Prepare(line[23 + start]) # Check left 0
            study_broken=Prepare(line[24 + start]).capitalize()
            study_broken_year=line[25 + start] # last year completed
            profstatus=Prepare(line[26 + start])[0:128].capitalize() # max 128 char
            #current_profession
            current_partner=Prepare(line[27 + start]).title()
            current_partner_dimension=Prepare(line[28 + start]).capitalize() # m2o relation ex. "Media impresa"
            attendant_hour=line[29 + start]   # Calculated field?
            attendant_passed=line[30 + start] # Evaluate boolean (format?)
            # Country?
            # partner_id link?
            comment= "Progetto: " + project_id + " - Editione: " + edition_id
            studysheet_id= CreateSchoolSheet(dbname,uid,pwd,studysheet)
            sex_id= getGender(dbname,uid,pwd,sex)
            #title_currentprof_id=CreateCurrentProfession(dbname,uid,pwd,current_profession)   
            title_profstatus_id=CreateCurrentProfessionStatus(dbname,uid,pwd,profstatus)   
            # Start of importation:
            counter['tot'] += 1  

            # test if record exists (basing on Ref. as code of Partner)
            item = sock.execute(dbname, uid, pwd, 'res.partner.contact', 'search', [('import', '=', ref)])

            if item:  # partner already exist
               counter['upd'] += 1  
               try:                   
                  data = {'name': surname,                
                          'first_name': name,     
                          'domain': domain,   
                          'office_id': office_id, 
                          'mobile': mobile, 
                          #'title_school_id': studysheet_id,   
                          #'gender': sex_id,    
                          #'disadvantage': disadvantage,  
                          #'title_currentprof_id':title_currentprof_id,   
                          #'title_profstatus_id': title_profstatus_id,
                          #'study_broken_year': study_broken_year,
                          #'study_broken': study_broken,  
                          #'section_id': team_id,
                          #'category_id':[(6,0,[categorie['c_if']])],
                          'comment': comment,
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
                  data={'name': surname,
                        'first_name': name,
                        'birthdate': birthdate,
                        #'sex':,
                        'office_id': office_id, 
                        'domain': domain,  
                        'birthplace': birthplace + "(" + birthprov + ")",
                        'fiscal_id_code': fiscalcode,                         
                        'mobile': mobile,
                        'import': ref,
                        'gender': sex_id,    
                        'title_school_id':  studysheet_id,  
                        'disadvantage': disadvantage,     
                        'title_profstatus_id': title_profstatus_id,
                        'study_broken_year': study_broken_year,
                        'study_broken': study_broken,  
                        'comment': comment,
                        }
                  ins_id_contact=sock.execute(dbname, uid, pwd, 'res.partner.contact', 'create', data)

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
               except:
                  print "*************************************************************"
                  print "[ERROR] Error creating data, current record: ", data
                  print "*************************************************************"
                  raise  # normal text of error

except:
    print '>>> [ERROR] Error importing data!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Total line: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
