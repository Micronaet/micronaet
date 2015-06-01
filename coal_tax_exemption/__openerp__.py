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
    'name' : 'Coal tax exemption',
    'version' : '0.0.1',
    'category' : 'Generic Modules/Customization',
    'description' : """Module for manage exemption on coal product in Italy
                       this module manage product material (marked as coal)
                       with a 'commercial register' and an 'internal register'
                       The movement of material is only IN, OUT or PRODUCTION
                       this module print 'DIA' report when coal product go in 
                       production and print 'Commercial report' for movement in 
                       stock location (for coal product)
                       There's also the 'wet manage' for in/out/production 
                       operations  
                    """,
    'author' : 'Micronaet s.r.l.',
    'website' : 'http://www.micronaet.it',
    'depends' : [
                 'base',
                 'product',
                 'sale',
                 'mrp',
                 'report_aeroo',
                 'report_aeroo_ooo',
                ],
    'init_xml' : [], 
    'update_xml' : [
                    'security/coal_group.xml',
                    'security/ir.model.access.csv',
                    
                    'coal_sequence.xml',    # sequence for counters
                    'coal_views.xml',                    
                    'coal_dashboard.xml',
                    
                    'report/via_report.xml',
                    'report/via_bf_report.xml',
                    'report/commercial_report.xml',
                    'report/internal_report.xml',
                    
                    'wizard/wizard_report_view.xml',
                   ],
    'demo_xml' : [],
    'active' : False, 
    'installable' : True, 
}
