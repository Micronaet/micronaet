# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import erppeek
import xlrd
import ConfigParser

# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
# From config file:
cfg_file = os.path.expanduser('../openerp.cfg')

config = ConfigParser.ConfigParser()
config.read([cfg_file])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint

# -----------------------------------------------------------------------------
# Utility:
# -----------------------------------------------------------------------------
def clean_field(value):
    ''' Clean extra space
    '''
    try:
        value = value or ''
        value = value.strip()
        return value
    except: 
        return value    

# -----------------------------------------------------------------------------
# Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (
        server, port), 
    db=dbname,
    user=user,
    password=pwd,
    )
product_pool = odoo.model('product.product')	
pedimento_pool = odoo.model('product.product.pedimento')	

import pdb; pdb.set_trace()
pedimento_ids = pedimento_pool.search([])
for pedimento in pedimento_pool.browse(pedimento_ids):
    name = pedimento.name
    code = name.replace(' ', '')
    product_id = pedimento.product_id.id
    double_ids = pedimento_pool.search([
        ('product_id', '=', product_id),
        ('code', '=', code),
        ])
    if double_ids:
        print 'Not updated: %s' % code
    else:
        pedimento_pool.write(pedimento.id, {
            'code': code,
            })    
    
    
