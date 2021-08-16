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
import pdb
import ConfigParser
import xlrd

# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
cfg_file = os.path.expanduser('../openerp.cfg')
config = ConfigParser.ConfigParser()
config.read([cfg_file])

# ERP Connection:
filename = './data/status.xlsx'
odoo = {
    'database': config.get('dbaccess', 'dbname'),
    'user': config.get('dbaccess', 'user'),
    'password': config.get('dbaccess', 'pwd'),
    'server': config.get('dbaccess', 'server'),
    'port': config.get('dbaccess', 'port'),
}

# -----------------------------------------------------------------------------
# Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (odoo['server'], odoo['port']),
    db=odoo['database'],
    user=odoo['user'],
    password=odoo['password'],
)

# Setup context for order:
product_pool = odoo.model('product.product')

# -----------------------------------------------------------------------------
# Load force name (for web publish)
# -----------------------------------------------------------------------------
try:
    WB = xlrd.open_workbook(filename)
except:
    print('Cannot read XLSX files: %s' % filename)
    sys.exit()

# -----------------------------------------------------------------------------
# Loop on all pages:
# -----------------------------------------------------------------------------
for ws_name in WB.sheet_names():
    WS = WB.sheet_by_name(ws_name)
    print('Read page: %s' % ws_name)

    start = False
    i = 0
    for row in range(WS.nrows):
        i += 1
        # ---------------------------------------------------------------------
        # Read product code:
        # ---------------------------------------------------------------------
        item_id = WS.cell(row, 0).value
        if item_id == 'ID':
            start = True
            print('%s. Find header line' % i)
            continue
        if not start:
            print('%s. Jump line not used' % i)
            continue
        item_id = int(item_id)

        # Original value:
        pdb.set_trace()
        excluded = WS.cell(row, 1).value.upper()
        excluded = excluded and excluded in 'SX'
        day_leadtime = WS.cell(row, 2).value
        day_min_level = WS.cell(row, 3).value

        # New value:
        new_excluded = WS.cell(row, 4).value.upper()
        new_excluded = new_excluded and new_excluded in 'SX'

        new_day_leadtime = WS.cell(row, 11).value
        new_day_min_level = WS.cell(row, 12).value

        if (excluded == new_excluded and
                day_leadtime == new_day_leadtime and
                day_min_level == new_day_min_level):
            print('%s. No change' % i)
            continue
        try:
            product_pool.write([item_id], {
                'not_in_status': new_excluded,
                'day_leadtime': new_day_leadtime,
                'day_min_level': new_day_min_level,
            })
            print('%s. Update record' % i)
        except:
            print('%s. Error updating record' % i)
            continue
print('Importazione terminata')
