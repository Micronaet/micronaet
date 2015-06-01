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
    'name' : 'Sale quotation webkit report',
    'version' : '0.0.1',
    'category' : 'Generic Modules/Customization',
    'description' : """Add an alternative report instead of RML one's
                    """,
    'author' : 'Micronaet s.r.l.',
    'website' : 'http://www.micronaet.it',
    'depends' : [
                 'base',
                 'sale',
                 #'email_template',
                 #'report_webkit',
                 'crm_quotation',
                ],
    'init_xml' : [], 
    'update_xml' : [
                    'sale_views.xml',
                    #'report/sale_webkit.xml',
                    #'data/sale_mail_template.xml', #not for now(change button)
                   ],
    'demo_xml' : [],
    'active' : False, 
    'installable' : True, 
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
