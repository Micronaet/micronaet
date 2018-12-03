# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import pyodbc
import erppeek
import ConfigParser

# -----------------------------------------------------------------------------
#                                UTILITY
# -----------------------------------------------------------------------------
def get_erp(URL, database, user, password):
    ''' Connect to log table in ODOO
    '''
    return erppeek.Client(
        URL,
        db=database,
        user=user,
        password=password,
        )   

# -----------------------------------------------------------------------------
#                                Parameters
# -----------------------------------------------------------------------------
# Extract config file name from current name
path, name = os.path.split(os.path.abspath(__file__))
fullname = os.path.join(path, 'openerp.cfg')

config = ConfigParser.ConfigParser()
config.read([fullname])

# DSN block:
dsn = config.get('dsn', 'name') 
uid = config.get('dsn', 'uid') 
pwd = config.get('dsn', 'pwd') 

# OpenERP block:
hostname = config.get('openerp', 'server')
port = config.get('openerp', 'port')
database = config.get('openerp', 'database')
user = config.get('openerp', 'user')
password = config.get('openerp', 'password')

URL = 'http://%s:%s' % (hostname, port) 

# Access MS SQL Database customer table:
connection = pyodbc.connect('DSN=%s;UID=%s;PWD=%s' % (dsn, uid, pwd))
cr = connection.cursor()

# OPENERP Obj: 
erp = get_erp(URL, database, user, password)

# -----------------------------------------------------------------------------
# UOM data:
# -----------------------------------------------------------------------------
import pdb; pdb.set_trace()
uom_pool = erp.ProductUom
uom_db = {}
query = ''' 
    SELECT CIDUNIDAD, CNOMBREUNIDAD 
    FROM dbo.admTiposCambio;
    '''
try:
    cr.execute(query)
except:
    print 'Error: %s' % (sys.exc_info(), )

for row in cr.fetchall():
    contipaq_id = row[0]
    contipaq_name = row[1]
    uom_ids = uom_pool.search([
        ('contipaq_ref', '=', contipaq_name)])
    if uom_ids:
        uom_db[contipaq_id] = uom_ids[0]
    else:
        print 'UOM: %s not found on ODOO' % contipaq_name    

# -----------------------------------------------------------------------------
# Read partner:
# -----------------------------------------------------------------------------
query = '''
    SELECT 
        CIDPRODUCTO, CCODIGOPRODUCTO, CNOMBREPRODUCTO, CTIPOPRODUCTO, 
        CIDUNIDADBASE
    FROM dbo.admProductos;
    '''
try:
    cr.execute(query)
except:
    print 'Error: %s' % (sys.exc_info(), )

product_pool = erp.ProductProduct

import pdb; pdb.set_trace()
for row in cr.fetchall():
    item_id = row[0]
    default_code = row[1]
    name = row[2]
    product_type = row[3]
    contipaq_uom_id = row[4]

    data = {
        'default_code': default_code,
        'name': name,
        }
    
    product_ids = product_pool.search([('default_code', '=', default_code)])
    if product_ids:
        product_pool.write(product_ids, data)
        print 'Update: %s' % name
    else:
        product_pool.create(data)
        print 'Insert: %s' % name
    
    # Update UOM via command line:
    query = '''
        update 
        '''
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
