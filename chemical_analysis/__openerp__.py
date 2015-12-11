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
    'name' : 'Chemicals product analysis',
    'version' : '0.0.1',
    'category' : 'Chemical / Analysis',
    'description' : """Module for manage chemical analysis for products
                       Link to 'in' stock move: every product get his form for
                       write his spectrographic analysis (and linked document
                       for supplier version)
                    """,
    'author' : 'Micronaet s.r.l.',
    'website' : 'http://www.micronaet.it',
    'depends' : [
        'base',
        'product',
        'stock',
        'report_aeroo',
        'report_aeroo_ooo',
    ],
    'init_xml' : [
        'data/chemical_element.xml',
    ], 
    'update_xml' : [
        'security/analysis_group.xml',
        'security/ir.model.access.csv',
        
        'wizard/duplicate_model_view.xml',

        'chemical_sequence.xml',
        'analysis_views.xml',   
                         
        'wizard/search_product_view.xml',
        'wizard/update_model_view.xml',
    ],
    'demo_xml' : [],
    'active' : False, 
    'installable' : True, 
}
