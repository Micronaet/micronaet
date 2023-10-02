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
    """ Connect to log table in ODOO
    """
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
uom_pool = erp.ProductUom
uom_db = {}
query = ''' 
    SELECT CIDUNIDAD, CNOMBREUNIDAD 
    FROM dbo.admUnidadesMedidaPeso;
    '''
try:
    cr.execute(query)
except:
    print('Error: %s' % (sys.exc_info(), ))

for row in cr.fetchall():
    print row
    contipaq_id = row[0]
    contipaq_name = row[1].strip()
    uom_ids = uom_pool.search([
        ('contipaq_ref', '=', contipaq_name)])
    if uom_ids:
        uom_db[contipaq_id] = uom_ids[0]
    else:
        print 'UOM: %s not found on ODOO' % contipaq_name

# -----------------------------------------------------------------------------
# Read partner:
# -----------------------------------------------------------------------------
cr = connection.cursor()
query = '''
    SELECT 
        CIDPRODUCTO, CCODIGOPRODUCTO, CNOMBREPRODUCTO, CTIPOPRODUCTO, 
        CIDUNIDADBASE
    FROM dbo.admProductos;
    '''
try:
    cr.execute(query)
except:
    print u'Error: %s' % (sys.exc_info(), )

product_pool = erp.ProductProduct

update_uom = []
all_product_ids = product_pool.search([
    ('sql_import', '=', True),
])
print('Total product imported found: %s' % len(all_product_ids))
for row in cr.fetchall():
    print row,
    item_id = row[0]
    default_code = row[1]
    name = row[2]
    product_type = row[3]
    contipaq_uom_id = row[4]

    data = {
        'default_code': default_code,
        'name': name,
        'sql_import': True,
        }

    product_ids = product_pool.search([('default_code', '=', default_code)])

    if product_ids:
        if len(product_ids) > 1:
            print('ERROR: More code: %s' % default_code)

        # Remove code found:
        for remove_id in product_ids:
            if remove_id in all_product_ids:
                all_product_ids.remove(remove_id)

        product_id = product_ids[0]
        product_pool.write(product_id, data)
        print(u' >> Update: %s' % name)
    else:
        product_id = product_pool.create(data)
        print(u' >> Insert: %s' % name)

        # Remove code found:
        if product_id in all_product_ids:
            all_product_ids.remove(product_id)

    uom_id = uom_db.get(contipaq_uom_id, False)
    if uom_id:
        update_uom.append((product_id, uom_id))

print(update_uom)
product_pool.update_uom(update_uom)

if all_product_ids:
    product_pool.write(all_product_ids, {
        'active': False,
        })
    print('Total product hidden: %s' % len(all_product_ids))

