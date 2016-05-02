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
{
    'name': 'Product ADR',
    'version': '0.0.1',
    'category': 'Generic Modules/Customization',
    'description': '''
        Module for add a check in product list for ADR product
           (this is important for offer and other documents)
        ''',
    'author': 'Micronaet s.r.l.',
    'website': 'http://www.micronaet.it',
    'depends': [
        'base',
        'product',
        'sale',
        'oil_duty', # Moved here all product.product.duty ref.
    ],
    'init_xml': [],
    'data': [
        'product_views.xml',
    ],
    'demo_xml': [],
    'active': False,
    'installable': True,
}
