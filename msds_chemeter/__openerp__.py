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
    'name': 'MSDS Chemeter',
    'version': '0.1',
    'category': '',
    'description': """
        Manage MSDS Chemeter form
        Module for import PDF file generated from external 
        program Chemeter ®
        All forms are manage there and imported scheduled
        """,
    'author': 'Micronaet S.r.l.',
    'website': 'https://micronaet.com',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'product',
        'save_as',
        'sapnaet',
        'sapnaet_ddt',
        ],
    'init_xml': [],
    'demo': [],
    'data': [
        'security/msds_group.xml',
        'security/ir.model.access.csv',
        'wizard/print_msds_form_wizard_view.xml',
        'msds_view.xml',
        'scheduler.xml',
        ],
    'active': False,
    'installable': True,
    'auto_install': False,
    }

