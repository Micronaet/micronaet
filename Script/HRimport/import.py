#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Modules used for ETL - Create User

# Modules required:
import os
import xmlrpclib, sys, csv, ConfigParser
from openerp.tools.status_history import status
from datetime import datetime

# -----------------------------------------------------------------------------
#           Set up parameters (for connection to Open ERP Database)
# -----------------------------------------------------------------------------
# Startup from config file:
config = ConfigParser.ConfigParser()
file_config = os.path.expanduser('~/etl/gfc/openerp.cfg')
config.read([file_config])
dbname = config.get('dbaccess','dbname')
user = config.get('dbaccess','user')
pwd = config.get('dbaccess','pwd')
server = config.get('dbaccess','server')
port = config.get('dbaccess','port')   # verify if it's necessary: getint
separator = eval(config.get('dbaccess','separator')) # test
log_only_error = eval(config.get('log','error')) # log only error in function

# Startup from code:
default_error_data = "2014/05/30"
log_file = os.path.expanduser("~/etl/gfc/log/%s.txt" % (datetime.now()))
log = open(log_file, 'w')

# -----------------------------------------------------------------------------
#                           XMLRPC connection
# -----------------------------------------------------------------------------
sock = xmlrpclib.ServerProxy(
    'http://%s:%s/xmlrpc/common' % (server, port), allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy(
    'http://%s:%s/xmlrpc/object' % (server, port), allow_none=True)

# -----------------------------------------------------------------------------
#                             Utility function
# -----------------------------------------------------------------------------
def format_string(valore):
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def format_date(valore,date=True):
    ''' Formatta nella data di PG
    '''
    try:
        if date:
            valore = valore.strip()
            #gma = valore.split(' ')[0].split('-') # only date (not time)
            return valore #'%s-%02d-%02d' % (gma[2], int(gma[1]), int(gma[0]))
    except:
        return False

def format_currency(valore):
    ''' Formatta nel float per i valori currency
    '''
    try:
        return float(valore)
    except:
        return 0.0
        
def format_boolean(value):
    ''' Formatta le stringhe '0' e '1' in boolean True e False
    '''
    return value == '1'

def log_event(*event):
    ''' Log event and comunicate with print
    '''
    if log_only_error and event[0][:5] == "[INFO":
        return
        
    log.write("%s. %s\r\n" % (datetime.now(), event))
    print event
    return

def create_partner(partner_code, type_of_partner, default_dict):
    ''' Create simple element for partner not found
        (write after in default_dict new element)
    '''
    try:
        field = "sql_%s_code" % type_of_partner      
        partner_ids = sock.execute(dbname, uid, pwd, "res.partner", "search", 
            [(field, '=', partner_code)])
        if partner_ids:
            partner_id = partner_ids[0]
        else:   
            data = {
                'name': "Partner %s (from migration)" % (partner_code),
                field: partner_code,
                }
            if type_of_partner == 'customer':
                data['ref'] = partner_code
                data['customer'] = True                
            elif type_of_partner == 'supplier':
                data['supplier'] = True
            elif type_of_partner == 'destination':
                data['is_address'] = True
                
            partner_id = sock.execute(dbname, uid, pwd, "res.partner",
                'create', data)
            log_event("[WARN] %s partner created: %s" % (type_of_partner, partner_code))
                
        default_dict[partner_code] = partner_id
        return partner_id
    except:
        log_event("[ERROR] Error creating %s partner: %s" % (type_of_partner, partner_code))
        return False
            

def get_or_create_partner(partner_code, type_of_partner, mandatory, res_partner_customer, res_partner_supplier):
    ''' Try to get partner element or create a simple element if not present
    '''    
    if type_of_partner == 'customer':
        default_dict = res_partner_customer 
    elif type_of_partner == 'supplier':
        default_dict = res_partner_supplier
    elif type_of_partner == 'destination': 
        default_dict = res_partner_customer # search in customer dict 
    else:
        default_dict = {} # nothing
        
    partner_id = default_dict.get(partner_code, False)

    if not partner_id: # create e simple element
        partner_id = create_partner(partner_code, type_of_partner, default_dict)
        
        
                  
    if mandatory and not partner_id:
        log_event("[ERROR] %s partner not found: %s" % (
            type_of_partner, partner_code))
    return partner_id    
        
# -----------------------------------------------------------------------------
#                            RES.PARTNER
# -----------------------------------------------------------------------------
only_create = True
jump_because_imported = True

file_input = os.path.expanduser('~/etl/gfc/res_partner')
openerp_object = 'res.partner'
log_event("Start import %s (customer)" % openerp_object)
res_partner_customer = {}
lines = csv.reader(open(file_input, 'rb'), delimiter=separator)
counter = {'tot': -2, 'new': 0, 'upd': 0}
max_cols = False
try:
    for line in lines:
        if jump_because_imported:
            break
        if counter['tot'] < 0:
            counter['tot'] += 1
            if not max_cols:
                max_cols = len(line)
            continue
        counter['tot'] += 1
        if len(line) != max_cols:
            log_event("[ERROR] %s Jumped line (col problem)" % counter['tot'])
            continue
            
        access_c_id = line[0].strip()
        name = format_string(line[13]).strip()
        code = format_string(line[18]).strip()
        
        # Start of importation:

        # test if record exists (basing on Ref. as code of Partner)
        search_key = 'ref' #'sql_customer_code' if code[:2] == '06' else 'sql_destination_code'
        item = sock.execute(
            dbname, uid, pwd, openerp_object , 'search', [
                #('access_c_id', '=', access_c_id),
                (search_key, '=', code),
        ])

        data = {
            'name': name,
            'is_company': True,
            'ref': code, #'access_c_id': access_c_id,
            'customer': True,                
            # for link sql importation
            #'sql_customer_code': code,
            #'sql_import': True,
        }
            
        if item:
           counter['upd'] += 1
           try:
               if only_create: 
                   log_event(
                       "[INFO]", counter['tot'], "Write", openerp_object, 
                       " (jumped only_create clause: ", code)
               else:    
                   item_mod = sock.execute(
                       dbname, uid, pwd, openerp_object, 'write', item, 
                       data)
                   log_event(
                       "[INFO]", counter['tot'], "Write", openerp_object, 
                       name)
               res_partner_customer[access_c_id] = item[0]
           except:
               log_event("[ERROR] Modifing data, current record:", data)

        else:
           counter['new'] += 1
           try:
               openerp_id = sock.execute(
                   dbname, uid, pwd, openerp_object, 'create', data)
               log_event(
                   "[INFO]", counter['tot'], "Create", openerp_object, 
                   code)
               res_partner_customer[access_c_id] = openerp_id
           except:
               log_event(
                   "[ERROR] Error creating data, current record: ", data)
except:
    log_event('[ERROR] Error importing data!')
    raise

store = status('%sc' % openerp_object)
if jump_because_imported:
    res_partner_customer = store.load()
else:
    store.store(res_partner_customer)
log_event("Total %(tot)s (N: %(new)s, U: %(upd)s)" % counter)

# -----------------------------------------------------------------------------
#                         RES.USERS
# -----------------------------------------------------------------------------
only_create = True
jump_because_imported = True

file_input = os.path.expanduser('~/etl/gfc/res_users')
openerp_object = 'res.users'
log_event("Start import %s" % openerp_object)
res_users = {}
lines = csv.reader(open(file_input, 'rb'), delimiter=separator)
counter = {'tot': -2, 'new': 0, 'upd': 0}
max_cols = False
try:
    for line in lines:
        if jump_because_imported:
            break
        if counter['tot'] < 0:
            counter['tot'] += 1
            if not max_cols:
                max_cols = len(line)
            continue
        counter['tot'] += 1
        if len(line) != max_cols:
            log_event("[ERROR] %s Jumped line (col problem)" % counter['tot'])
            continue
        access_id = line[0].strip()
        name = format_string(line[1])
        #date = format_date(line[2])
        active = format_boolean(line[2])
        login = format_string(line[3])
        password = format_string(line[4])

        # Anagrafiche semplici:
        #origin_id = origin.get(origin_code, False)

        # Start of importation:
        counter['tot'] += 1

        data = {
            'name': name,
            'login': login,
            'password': password,
        }

        # test if record exists (basing on Ref. as code of Partner)
        item = sock.execute(dbname, uid, pwd, openerp_object , 'search', [
            ('login', '=', login)])
            
        if item:  # already exist
           counter['upd'] += 1
           try:
               if only_create: 
                   log_event(
                       "[INFO]", counter['tot'], "Write", 
                       openerp_object, ", jumped only_create clause: ", 
                       data)
               else:    
                   try:
                       item_mod = sock.execute( 
                           dbname, uid, pwd, openerp_object, 'write', 
                           item, data)
                       log_event(
                           "[INFO]", counter['tot'], "Write", 
                           openerp_object, data)
                   except:
                       log_event(
                           "[ERR] %s Write data %s", counter['tot'], data)
                               
               res_users[access_id] = item[0]
           except:
               log_event("[ERROR] Modifing data, current record:", data)
        else:   # new
           counter['new'] += 1
           try:
               openerp_id = sock.execute(
                   dbname, uid, pwd, openerp_object, 'create', data)
               log_event(
                   "[INFO]b", counter['tot'], "Create", 
                   openerp_object, data)
               res_users[access_id] = openerp_id
           except:
               log_event(
                   "[ERROR] Error creating data, current record: ", data)

except:
    log_event('[ERROR] Error importing data!')
    raise
store = status(openerp_object)
if jump_because_imported:
    res_users = store.load()
else:
    store.store(res_users)    
log_event("Total %(tot)s (N: %(new)s, U: %(upd)s)" % counter)

# -----------------------------------------------------------------------------
#                         HR.EMPLOYEE
# -----------------------------------------------------------------------------
only_create = True
jump_because_imported = True

file_input = os.path.expanduser('~/etl/gfc/hr_employee')
openerp_object = 'hr.employee'
log_event("Start import %s" % openerp_object)
hr_employee = {}
lines = csv.reader(open(file_input, 'rb'), delimiter=separator)
counter = {'tot': -2, 'new': 0, 'upd': 0}
max_cols = False

try:
    for line in lines:
        if jump_because_imported:
            break
        if counter['tot'] < 0:
            counter['tot'] += 1
            if not max_cols:
                max_cols = len(line)
            continue
        counter['tot'] += 1
        if len(line) != max_cols:
            log_event("[ERROR] %s Jumped line (col problem)" % counter['tot'])
            continue
        access_id = line[0].strip()
        marital = format_string(line[7])
        active = format_boolean(line[8])
        #birthday = format_string(line[9])
        #work_email = format_string(line[10])
        #work_location = format_string(line[14])
        user_code = format_string(line[14])
        name = format_string(line[15])
        #work_phone = format_string(line[14])
        #gender = format_string(line[14])
        #parent_code = format_string(line[18])
        #category_code = format_string(line[19])

        # Anagrafiche semplici:
        if not user_code:
            log_event("[ERROR] %s No user code" % counter['tot'])
            continue
            
        user_id = res_users.get(user_code, False)

        # Start of importation:
        counter['tot'] += 1

        data = {
            'name': name,
            'user_id': user_id,
        }

        # test if record exists (basing on Ref. as code of Partner)
        item = sock.execute(dbname, uid, pwd, openerp_object , 'search', [
            ('name', '=', name)])
            
        if item:  # already exist
           counter['upd'] += 1
           try:
               if only_create: 
                   log_event(
                       "[INFO]", counter['tot'], "Write", 
                       openerp_object, ", jumped only_create clause: ", 
                       data)
               else:    
                   try:
                       item_mod = sock.execute( 
                           dbname, uid, pwd, openerp_object, 'write', 
                           item, data)
                       log_event(
                           "[INFO]", counter['tot'], "Write", 
                           openerp_object, data)
                   except:
                       log_event(
                           "[ERR] %s Write data %s", counter['tot'], data)
                               
               hr_employee[access_id] = item[0]
           except:
               log_event("[ERROR] Modifing data, current record:", data)
        else:   # new
           counter['new'] += 1
           try:
               openerp_id = sock.execute(
                   dbname, uid, pwd, openerp_object, 'create', data)
               log_event(
                   "[INFO]", counter['tot'], "Create", 
                   openerp_object, data)
               hr_employee[access_id] = openerp_id
           except:
               log_event(
                   "[ERROR] Error creating data, current record: ", data)

except:
    log_event('[ERROR] Error importing data!')
    raise
store = status(openerp_object)
if jump_because_imported:
    hr_employee = store.load()
else:
    store.store(hr_employee)    
log_event("Total %(tot)s (N: %(new)s, U: %(upd)s)" % counter)

# -----------------------------------------------------------------------------
#                         ACCOUNT.ANALYTIC.ACCOUNT
# -----------------------------------------------------------------------------
only_create = True
jump_because_imported = True

file_input = os.path.expanduser('~/etl/gfc/account_analytic_account')
openerp_object = 'account.analytic.account'
log_event("Start import %s" % openerp_object)
account_analytic_account = {}
lines = csv.reader(open(file_input, 'rb'), delimiter=separator)
counter = {'tot': -2, 'new': 0, 'upd': 0}
max_cols = False

try:
    for line in lines:
        if jump_because_imported:
            break
        if counter['tot'] < 0:
            counter['tot'] += 1
            if not max_cols:
                max_cols = len(line)
            continue
        counter['tot'] += 1
        if len(line) != max_cols:
            log_event("[ERROR] %s Jumped line (col problem)" % counter['tot'])
            continue
        access_id = line[0].strip()
        code = format_string(line[5])
        active = format_boolean(line[9])
        partner_code = format_string(line[13])
        user_code = format_string(line[14])
        name = format_string(line[13])

        user_id = res_users.get(user_code, False)
        partner_id = res_partner_customer.get(partner_code, False)

        # Start of importation:
        counter['tot'] += 1

        data = {
            'code': code,
            'name': name,
            'user_id': user_id,
            'partner_id': partner_id,
            'use_timesheets': True,
        }

        # test if record exists (basing on Ref. as code of Partner)
        item = sock.execute(dbname, uid, pwd, openerp_object , 'search', [
            ('code', '=', code)])
            
        if item:  # already exist
           counter['upd'] += 1
           try:
               if only_create: 
                   log_event(
                       "[INFO]", counter['tot'], "Write", 
                       openerp_object, ", jumped only_create clause: ", 
                       data)
               else:    
                   try:
                       item_mod = sock.execute( 
                           dbname, uid, pwd, openerp_object, 'write', 
                           item, data)
                       log_event(
                           "[INFO]", counter['tot'], "Write", 
                           openerp_object, data)
                   except:
                       log_event(
                           "[ERR] %s Write data %s", counter['tot'], data)
                               
               account_analytic_account[access_id] = item[0]
           except:
               log_event("[ERROR] Modifing data, current record:", data)
        else:   # new
           counter['new'] += 1
           try:
               openerp_id = sock.execute(
                   dbname, uid, pwd, openerp_object, 'create', data)
               log_event(
                   "[INFO]", counter['tot'], "Create", 
                   openerp_object, data)
               account_analytic_account[access_id] = openerp_id
           except:
               log_event(
                   "[ERROR] Error creating data, current record: ", data)

except:
    log_event('[ERROR] Error importing data!')
    raise
store = status(openerp_object)
if jump_because_imported:
    account_analytic_account = store.load()
else:
    store.store(account_analytic_account)    
log_event("Total %(tot)s (N: %(new)s, U: %(upd)s)" % counter)

# -----------------------------------------------------------------------------
#                         PRODUCT.PRODUCT
# -----------------------------------------------------------------------------
only_create = True
jump_because_imported = True

file_input = os.path.expanduser('~/etl/gfc/product_template')
openerp_object = 'product.product'
log_event("Start import %s" % openerp_object)
product_product = {}
lines = csv.reader(open(file_input, 'rb'), delimiter=separator)
counter = {'tot': -2, 'new': 0, 'upd': 0}
max_cols = False

try:
    for line in lines:
        if jump_because_imported:
            break
        if counter['tot'] < 0:
            counter['tot'] += 1
            if not max_cols:
                max_cols = len(line)
            continue
        counter['tot'] += 1
        if len(line) != max_cols:
            log_event("[ERROR] %s Jumped line (col problem)" % counter['tot'])
            continue
        access_id = line[0].strip()
        name = format_string(line[18])

        # Start of importation:
        counter['tot'] += 1

        data = {
            'description_sale': access_id,
            'name': name,
            'company_id': 1,
            #'cost_method': 'standard',
            'sale_ok': True,
            #'procure_method': 'make_to_stock',
            #'supply_method': 'supply_method',
            #'cost_method': 'standard',
            'type': 'service',
            'standard_price': 1.0,
            'list_price': 1.0,
        }

        # test if record exists (basing on Ref. as code of Partner)
        item = sock.execute(dbname, uid, pwd, openerp_object , 'search', [
            ('description_sale', '=', access_id)])
            
        if item:  # already exist
           counter['upd'] += 1
           try:
               if only_create:
                   log_event(
                       "[INFO]", counter['tot'], "Write", 
                       openerp_object, ", jumped only_create clause: ", 
                       data)
               else:    
                   try:
                       item_mod = sock.execute( 
                           dbname, uid, pwd, openerp_object, 'write', 
                           item, data)
                       log_event(
                           "[INFO]", counter['tot'], "Write", 
                           openerp_object, data)
                   except:
                       log_event(
                           "[ERR] %s Write data %s", counter['tot'], data)
                               
               product_product[access_id] = item[0]
           except:
               log_event("[ERROR] Modifing data, current record:", data)
        else:   # new
           counter['new'] += 1
           try:
               openerp_id = sock.execute(
                   dbname, uid, pwd, openerp_object, 'create', data)
               log_event(
                   "[INFO]", counter['tot'], "Create", 
                   openerp_object, data)
               product_product[access_id] = openerp_id
           except:
               log_event(
                   "[ERROR] Error creating data, current record: ", data)

except:
    log_event('[ERROR] Error importing data!')
    raise
store = status(openerp_object)
if jump_because_imported:
    product_product = store.load()
else:
    store.store(product_product)    
log_event("Total %(tot)s (N: %(new)s, U: %(upd)s)" % counter)

# -----------------------------------------------------------------------------
#                         ACCOUNT.ANALYTIC.LINE
# -----------------------------------------------------------------------------
only_create = False
jump_because_imported = False

file_input = os.path.expanduser('~/etl/gfc/account_analytic_line')
openerp_object = 'hr.analytic.timesheet' #'account.analytic.line'
log_event("Start import %s" % openerp_object)
account_analytic_line = {}
lines = csv.reader(open(file_input, 'rb'), delimiter=separator)
counter = {'tot': -2, 'new': 0, 'upd': 0}
max_cols = False
import pdb; pdb.set_trace()
try:
    for line in lines:
        if jump_because_imported:
            break
        if counter['tot'] < 0:
            counter['tot'] += 1
            if not max_cols:
                max_cols = len(line)
            continue
        counter['tot'] += 1
        if len(line) != max_cols:
            log_event("[ERROR] %s Jumped line (col problem)" % counter['tot'])
            continue

        #if counter['tot'] >= 214:
        #    break
        access_id = line[0].strip()
        user_code = format_string(line[6])
        account_code = format_string(line[7])
        general_code = format_string(line[8])
        uom_code = format_string(line[9])
        journal_code = format_string(line[10])
        
        name = format_string(line[11])
        amount = format_currency(line[12])
        unit_amount = format_currency(line[13])
        date = format_date(line[14])
        product_code = format_string(line[17])

        user_id = res_users.get(user_code, False)
        account_id = account_analytic_account.get(account_code, False)
        #general_id = res_users.get(general_code, False)
        #uom_id = res_users.get(uom_code, False)
        #journal_id = res_users.get(journal_code, False)
        product_id = product_product.get(product_code, False)
        if not product_id:
            log_event("[ERROR] %s No product" % counter['tot'])
            continue
            

        # Start of importation:
        counter['tot'] += 1

        data = {
            'name': name,
            'user_id': user_id,
            'product_id': product_id,
            'account_id': account_id,
            'date': date,
            'amount': amount,
            'unit_amount': unit_amount,
            'code': access_id,
            'general_account_id': 132,
            'journal_id': 3,
        }

        # test if record exists (basing on Ref. as code of Partner)
        item = sock.execute(dbname, uid, pwd, openerp_object , 'search', [
            ('code', '=', access_id)])
            
        if item:  # already exist
           counter['upd'] += 1
           try:
               if only_create: 
                   log_event(
                       "[INFO]", counter['tot'], "Write", 
                       openerp_object, ", jumped only_create clause: ", 
                       data)
               else:    
                   try:
                       item_mod = sock.execute( 
                           dbname, uid, pwd, openerp_object, 'write', 
                           item, data)
                       log_event(
                           "[INFO]", counter['tot'], "Write", 
                           openerp_object, data)
                   except:
                       log_event(
                           "[ERR] %s Write data %s", counter['tot'], data)
                               
               account_analytic_line[access_id] = item[0]
           except:
               log_event("[ERROR] Modifing data, current record:", data)
        else:   # new
           counter['new'] += 1
           try:
               openerp_id = sock.execute(
                   dbname, uid, pwd, openerp_object, 'create', data)
               log_event(
                   "[INFO]", counter['tot'], "Create", 
                   openerp_object, data)
               account_analytic_line[access_id] = openerp_id
           except:
               log_event(
                   "[ERROR] Error creating data, current record: ", data, sys.exc_info())

except:
    log_event('[ERROR] Error importing data!')
    raise
store = status(openerp_object)
if jump_because_imported:
    account_analytic_line = store.load()
else:
    store.store(account_analytic_line)    
log_event("Total %(tot)s (N: %(new)s, U: %(upd)s)" % counter)

log_event("End of importation")
