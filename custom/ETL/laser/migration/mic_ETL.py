#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules ETL Partner Scuola

# Modules required:
import sys
import time
import string
from mx.DateTime import now
import pickle

#### Generic function:
def cPickleParticOutput(file_name, data):
    output_f = open(file_name, 'wb')
    pickle.dump(data, output_f)
    output_f.close()

def cPickleParticInput(file_name):
    input_f = open(file_name, 'rb')
    data = pickle.load(input_f)
    input_f.close()
    return data

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

def getLanguage(sock,dbname,uid,pwd,name):
    # get Language if exist (use english name request 
    return sock.execute(dbname, uid, pwd, 'res.lang', 'search', [('name', '=', name),])[0]

#### Partner function
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

#### Contact function:
def CreateTitle(dbname,uid,pwd,titles,table):
    # Create standard title for partner (procedure batch from tupla, set up from user)
    for title in titles:
        title_id = sock.execute(dbname, uid, pwd, 'res.partner.title', 'search', [('name', '=', title)])
        if not len(title_id):            
           title_id=sock.execute(dbname,uid,pwd, 'res.partner.title', 'create',{'name': title, 
                                                                               'domain': table, 
                                                                               'shortcut': ShortCut(title),
                                                                              })  

def CreateOffice(sock,dbname,uid,pwd,name):
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

# Ufficio doti:
def CreateCCNL(sock,dbname,uid,pwd,name):
    # create or get CCNL ID
    if not name: return 
    search_id = sock.execute(dbname, uid, pwd, 'res.partner.contact.ccnl', 'search', [('name', '=', name),])
    if len(search_id): 
       return search_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'res.partner.contact.ccnl','create',{'name': name,})  

def CreateFormation(sock,dbname,uid,pwd,name):
    # create or get Formation ID
    if not name: return 
    search_id = sock.execute(dbname, uid, pwd, 'res.partner.contact.formation', 'search', [('name', '=', name),])
    if len(search_id): 
       return search_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'res.partner.contact.formation','create',{'name': name,})  

def CreatePIPstate(sock,dbname,uid,pwd,name):
    # create or get PIP state ID
    if not name: return 
    search_id = sock.execute(dbname, uid, pwd, 'res.partner.contact.pip', 'search', [('name', '=', name),])
    if len(search_id): 
       return search_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'res.partner.contact.pip','create',{'name': name,})  

def CreateProfile(sock,dbname,uid,pwd,name):
    # create or get Profile state ID
    if not name: return 
    search_id = sock.execute(dbname, uid, pwd, 'res.partner.contact.profile', 'search', [('name', '=', name),])
    if len(search_id): 
       return search_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'res.partner.contact.profile','create',{'name': name,})  

