# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) and the
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#    Copyright (c)2008-2010 SIA "KN dati".(http://kndati.lv)All Rights Reserved.
#                  General contacts <info@kndati.lv>
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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
    'name' : 'CRM Partner categorization',
    'version' : '0.0.1',
    'category' : 'Generic Modules/CRM & SRM',
    'description' : """CRM:
                       Partner categorization, add a field in partner contact
                       to let user decide how consider partner, after there
                       are a test activity on CRM events that with this field
                       put in evidence if partner is to be contact with a 
                       traffic lite view (3 colors)
                    """,
    'author' : 'Micronaet s.r.l.',
    'website' : 'http://www.micronaet.it',
    'depends' : [
                 'base',
                 'base_fiam',
                ],
    'init_xml' : [], 
    'update_xml' : ['security/ir.model.access.csv',
                    'categorization_view.xml',
                   ],
    'demo_xml' : [],
    'active' : False, 
    'installable' : True, 
}
