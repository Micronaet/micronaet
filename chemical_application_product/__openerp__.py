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
    'name' : 'Chemical application product',
    'version' : '0.0.1',
    'category' : 'Generic Modules/Analysis',
    'description' : """ Statistic and analysis of generic use that our customer
                        do for chemical product 
                        The module add some view to link for every customer
                        a list of product (one2many) and for each product
                        (one2many) add extra information for use of the product
                        so each product can have several use 
                        After this input phase we try to organize data for 
                        particular reverse statistic                        
                    """,
    'author' : 'Micronaet s.r.l.',
    'website' : 'http://www.micronaet.it',
    'depends' : ['base',
                 'product',
                 'sale',
                 'base_panchemicals',
                ],
    'init_xml' : [], 
    'update_xml' : [
                    'security/ir.model.access.csv',
                    'chemical_application_views.xml',
                   ],
    'demo_xml' : [],
    'active' : False, 
    'installable' : True, 
}
