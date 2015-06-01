# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) and the
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Dentist web',
    'version': '0.0.1',
    'category': 'Generic Modules/Customization',
    'description': """Modulo per gestire la demo sul web
                   """,
    'author': 'Micronaet s.r.l.',
    'website': 'http://www.micronaet.it',
    'depends': [
        'base',
        'dentist',
        ],
    'init_xml': [], 
    'update_xml': [
        'wizard/dentist_web_view.xml',
        'wizard/welcome_view.xml',
        ],
    'demo_xml': [
        ],
    'active': False, 
    'installable': True, 
}
