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

stock = []

# -----------------------------------------------------------------------------
# Pedimento stock:
# -----------------------------------------------------------------------------
print 'Start reading pedimento product'
cr.execute('sp_existence_Pedimento_Product')
for record in cr.fetchall():
    row = tuple(record)
    print row
    if row[2] != 'MP':        
        continue
    stock.append(row)

# -----------------------------------------------------------------------------
# Lot stock:
# -----------------------------------------------------------------------------
print 'Start reading lot product'
cr.execute('sp_existence_Product')
for record in cr.fetchall():
    row = tuple(record)
    print row
    if row[2] != 'MP':
        continue
    stock.append(row)

product_pool = erp.model('product.product')
product_pool.rpc_import_stock_status_mx(stock)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
