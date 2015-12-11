#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Modules ETL Fiam: collect of function
import sys, time, string
from mx.DateTime import now
import pickle

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

def PrepareFloat(valore):
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values

def getCountryFromCode(sock,dbname,uid,pwd,code):
    if code: 
       find_id = sock.execute(dbname, uid, pwd, 'res.country', 'search', [('code', '=', code),]) 
       if find_id: 
          return find_id[0] 
       else: 
          return False # TODO segnalare la mancanza della sigla
    else:
       return False # no code


def ShortCut(valore=''): 
    # used for code the title (partner or contact), ex.: Sig.ra > SIGRA
    if valore:
       valore = valore.upper()
       valore = valore.replace('.','')
       valore = valore.replace(' ','')
       return valore

def getTaxID(sock,dbname,uid,pwd,description):
    # get ID of tax from description value
    return sock.execute(dbname, uid, pwd, 'account.tax', 'search', [('description', '=', description),])[0]

def getLanguage(sock,dbname,uid,pwd,name):
    # get Language if exist (use english name request 
    return sock.execute(dbname, uid, pwd, 'res.lang', 'search', [('name', '=', name),])[0]

# PRODUCT
def getUomCateg(sock,dbname,uid,pwd,categ):
    # Create categ. for UOM
    cat_id = sock.execute(dbname, uid, pwd, 'product.uom.categ', 'search', [('name', '=', categ),]) 
    if len(cat_id): 
       return cat_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'product.uom.categ','create',{'name': categ,})  

def getUOM(sock,dbname,uid,pwd,name,data):
    # Create if not exist name: 'name' UOM with data: data{}
    uom_id = sock.execute(dbname, uid, pwd, 'product.uom', 'search', [('name', '=', name),]) 
    if len(uom_id): 
       return uom_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'product.uom','create',data)  

# PARTNER & CONTACT
def CreateTitle(sock,dbname,uid,pwd,titles,table):
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

def getRegion(sock,dbname,uid,pwd,region):
    # Get region ID of passed name (use "like" operator for Trentino and Emilia)
    region=region.strip()       
    region=region.title()            
    return sock.execute(dbname, uid, pwd, 'res.country.state', 'search', [('name','like',region)]) 

def CreateAllRegion(sock,dbname,uid,pwd,regions):
    # Create region as a res.country.state linked to Italy nation
    country_id = sock.execute(dbname, uid, pwd, 'res.country', 'search', [('name','=','Italy')]) 
    for region in regions:
        region_id = sock.execute(dbname, uid, pwd, 'res.country.state', 'search', [('name', '=', region),('country_id','=',country_id)])
        if not len(region_id):            
           region_id=sock.execute(dbname,uid,pwd, 'res.country.state', 'create',{'name': region.title(), 
                                                                                 'country_id': country_id[0], 
                                                                                 'code': region[0:3].upper(), # first 3 char
                                                                                })  
    return 
