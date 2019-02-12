#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
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

{
    'name': 'Production Line for Mexico',
    'version': '0.1',
    'category': 'MRP',
    'description': '''        
        Add different management for Mexico production
        ''',
    'author': 'Micronaet S.r.l. - Nicola Riolini',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [    
        'base',
        'production_line',
        'production_pedimento',
        'excel_export',
        ],
    'init_xml': [],
    'demo': [],
    'data': [
        'security/mx_group.xml',
        #'security/ir.model.access.csv',    
        'custom_mx_view.xml',
        'wizard/parameter_view.xml',
        'wizard/confirm_production_mx_wizard.xml',
        'scheduler.xml',        
        ],
    'active': False,
    'installable': True,
    'auto_install': False,
    }
