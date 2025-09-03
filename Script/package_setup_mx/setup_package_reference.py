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
import pdb
import erppeek
import ConfigParser

setup = {
    'start': [
        (['S', 'R'], ['B6010', 'B6008', 'B6015', 'B6009', 'B6006']),
        (['S', 'R', 'X'], ['TARIMA EXP']),
        (['O'],['TOTE']),
        ],
    'name': [
        (['PANFLUX'], ['FF'])
    ],
    'code': [
        (['S0444V--X', 'H5710', 'H5700V'], ['FF']),
    ],
}
    
# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
cfg_file = os.path.expanduser('../openerp.cfg')

config = ConfigParser.ConfigParser()
config.read([cfg_file])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint

# ----------------------------------------------------------------------------------------------------------------------
# Connect to ODOO:
# ----------------------------------------------------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (
        server, port),
    db=dbname,
    user=user,
    password=pwd,
    )


# ----------------------------------------------------------------------------------------------------------------------
# Extract package:
# ----------------------------------------------------------------------------------------------------------------------
ul_pool = odoo.model('product.ul')
package_pool = odoo.model('product.packaging')
product_pool = odoo.model('product.product')

for start_char in ('Z', 'M', 'A', 'B'):
    package_ids = package_pool.search([
        ('product_id.default_code', '=ilike', '{}%'.format(start_char)),
    ])
    print('Remove package for {} code #{}'.format(start_char, len(package_ids)))
    package_pool.unlink(package_ids)

# ----------------------------------------------------------------------------------------------------------------------
# Load UL database:
# ----------------------------------------------------------------------------------------------------------------------
ul_db = {}
ul_ids = ul_pool.search([
    ('linked_product_id', '!=', False),
    ])
for ul in ul_pool.browse(ul_ids):
    # code = ul.linked_product_id.default_code
    code = ul.code
    ul_db[code] = ul.id
print('UL database\n {}'.format(ul_db))

# ----------------------------------------------------------------------------------------------------------------------
# Master Loop:
# ----------------------------------------------------------------------------------------------------------------------
# Clean all:
package_ids = package_pool.search([
    ('is_active', '=', True),
])
print('Cleaning package #{}'.format(len(package_ids)))
package_pool.write(package_ids, {
    'is_active': False,
})

pdb.set_trace()
for mode in setup:
    print('>> MODE: {}'.format(mode))

    # ------------------------------------------------------------------------------------------------------------------
    # Mode product selection:
    # ------------------------------------------------------------------------------------------------------------------
    for code_part_list, ul_code_list in setup[mode]:
        for code_part in code_part_list:
            print('>> MODE: {} >> Code {}'.format(mode, code_part))

            if mode == 'start':
                product_ids = product_pool.search([
                    # ('product_type', '=', 'PT'),
                    ('default_code', '=ilike', '{}%'.format(code_part)),
                ])
            elif mode == 'code':
                product_ids = product_pool.search([
                    # ('product_type', '=', 'PT'),
                    ('default_code', '=', code_part),
                    ('default_code', 'not ilike', 'OLD'),
                ])
            elif mode == 'name':
                product_ids = product_pool.search([
                    # ('product_type', '=', 'PT'),
                    ('name', 'ilike', code_part),
                ])
            else:
                continue

            # ----------------------------------------------------------------------------------------------------------
            # Product Loop:
            # ----------------------------------------------------------------------------------------------------------
            for product_id in product_ids:
                print('>> MODE: {} >> Code {} >> Product ID {}'.format(mode, code_part, product_id))

                # ------------------------------------------------------------------------------------------------------
                # Package Loop:
                # ------------------------------------------------------------------------------------------------------
                for ul_code in ul_code_list:
                    ul_id = ul_db.get(ul_code)
                    if not ul_id:
                        print('Not found UL: {}'.format(ul_code))
                        continue

                    print('>> MODE: {} >> Code {} >> Product ID {} >> UL ID {}'.format(mode, code_part, product_id, ul_id))

                    # Search package-product:
                    package_active_ids = package_pool.search([
                        ('product_id', '=', product_id),
                        ('ul', '=', ul_id),
                        ('is_active', '=', True),
                        ])
                    package_unactive_ids = package_pool.search([
                        ('product_id', '=', product_id),
                        ('ul', '=', ul_id),
                        ('is_active', '=', False),
                        ])

                    # ------------------------------------------------------------------------------------------------------
                    # Setup product-package:
                    # ------------------------------------------------------------------------------------------------------
                    # Found unactive:
                    if package_unactive_ids:
                        # Present, set as active
                        package_pool.write(package_unactive_ids, {
                            'is_active': True,
                        })

                    # Not found:
                    elif not package_active_ids:
                        # Not present, create new one
                        package_pool.create({
                            'product_id': product_id,
                            'is_active': True,
                            'ul': ul_id,
                            # 'ul_qty': 0.0,
                        })
                    # else yet present and active
