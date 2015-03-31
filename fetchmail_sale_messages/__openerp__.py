# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
    'name' : 'Fetchmail sale messages',
    'version' : '0.0.1',
    'category' : 'Generic Modules/Customization',
    'description' : """Fetchmail for comunication for sale order
                       All mail generated for auto sending with ID: ##1## in
                       subject are parsed and auto linked to sale order
                       Every email is extract and his body became a message
                    """,
    'author' : 'Micronaet s.r.l.',
    'website' : 'http://www.micronaet.it',
    'depends' : [
                 'base',
                 'sale',
                 'poweremail',
                 'fetchmail',
                ],
    'init_xml' : [], 
    'update_xml' : [
                    'security/ir.model.access.csv',
                    'sale_views.xml',                    
                   ],
    'demo_xml' : [],
    'active' : False, 
    'installable' : True, 
}
