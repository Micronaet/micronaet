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
import pdb
import sys
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

# OpenERP block:
hostname = config.get('openerp', 'server')
port = config.get('openerp', 'port')
database = config.get('openerp', 'database')
user = config.get('openerp', 'user')
password = config.get('openerp', 'password')

URL = 'http://%s:%s' % (hostname, port)
erp = get_erp(URL, database, user, password)

product_pool = erp.model('product.product')
product_ids = product_pool.search([])
pdb.set_trace()
for product in product_pool.browse(product_ids):
    default_code = product.default_code or ''
    start_code = default_code[:1]
    if start_code and start_code in 'AB':
        print('Saltato: %s' % default_code)
        continue
    product.populate_packaging_update_all([product.id])
    print('Load package: %s' % default_code)

