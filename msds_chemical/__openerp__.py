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

{
    'name': 'MSDS Chemical',
    'version': '0.1',
    'category': '',
    'description': """
        Manage MSDS Chemicals form
        Module for import PDF file generated from external 
        program EpyPlus ®
        All forms are manage there in OpenERP are imported
        only PDF testing timestamp of file for get revision
        informations
        In OpenERP there's an automated mail depend on product
        buyed from customers
        """,
    'author': 'Micronaet S.r.l.',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'product',
        ],
    'init_xml': [],
    'demo': [],
    'data': [
        'security/msds_group.xml',
        'security/ir.model.access.csv',
        'msds_view.xml',
        'scheduler.xml',
        
        'data/list.xml',
        ],
    'active': False,
    'installable': True,
    'auto_install': False,
    }

