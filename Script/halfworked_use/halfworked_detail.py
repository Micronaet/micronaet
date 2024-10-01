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
# Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (
        server, port),
    db=dbname,
    user=user,
    password=pwd,
    )
mrp_pool = odoo.model('mrp.production')
mrp_ids = mrp_pool.search([
    ('accounting_state', '=', 'close'),
    ])

import pdb; pdb.set_trace()
data = {}
data_total = {}

# Collect data:
for mrp in mrp_pool.browse(mrp_ids):
    # Extract data:
    date = str(mrp.date_planned)[:10]
    year = date[:4]
    final_product = mpr.product_id.default_code

    for job in mrp.workcenter_lines:
        for material in job.bom_material_ids:
            # Extract data:
            material = material.product_id
            default_code = material.default_code or ''
            start = default_code[:1]
            quantity = material.quantity

            # Only final product:
            if start and start in 'AB':
                continue

            if default_code not in data:
                data[default_code] = ['', []]
                data_total[default_code] = {}

            if year not in data_total[default_code]:
                data_total[default_code][year] = 0.0

            if not data[default_code][0] or date > data[default_code][1]:
                data[default_code][1] = date

            data_total[default_code][year] += quantity

            data_total[default_code][1].append((
                date,
                quantity,
                job.name,
                final_product,
                ))

# -----------------------------------------------------------------------------
# Detail:
# -----------------------------------------------------------------------------
log_f = open('detail.csv', 'w')
log_f.write('Semilavorato|Ultimo uso|Data|Q.|Lavorazione|Prod. finito\n')
for default_code in sorted(data):
    last_date, data_detail = data[default_code]
    header_line = '%s|%s|' % (
        default_code, last_date)

    for record in sorted(data_detail, reversed=True):
        line = '%s|%s|%s|%s|%s\n' % (
            header_line,
            record[0],
            record[1],
            record[2],
            record[3],
        )
        print(line)
        log_f.write(line)

# -----------------------------------------------------------------------------
# Total:
# -----------------------------------------------------------------------------
log_f = open('total.csv', 'w')
log_f.write('Semilavorato|Ultimo uso|Anno|Q.\n')
for year in data:
    for default_code in sorted(data_total):
        for year in sorted(data_total[default_code]):
            quantity = data_total[default_code][year]
            last_use = data[default_code][0]
            log_f.write('%s|%s|%s|%s\n' % (
                default_code,
                last_use,
                year,
                quantity,
                ))

