# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                  General contacts <info@kndati.lv>
#    Copyright (c) 2008-2011 Micronaet s.r.l. (http://www.micronaet.it) All Rights Reserved.
#                    General contacts <info@micronaet.it>
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
    'name' : 'Label for Easylabel',
    'version' : '1.0.0',
    'category' : 'Generic/Label',
    'description' : """This module is made for manage the print program
                       called Easylabel by Tharo, his work is get a list of
                       label to do for a customer, find the related label to print
                       associated with partner, generate a "command file", as 
                       Easylabel call this file, so the print program can "batch"
                       print all the list of label without operator.
                       Any features: Same label are added, similar label for dimension
                       are grouped, for optimize change of the roll of label.
                    """,
    'author' : 'Micronaet s.r.l.',
    'website' : 'http://www.micronaet.it',
    'depends' : ['base', 'sale', 'product', 'report_aeroo'],
    'init_xml' : [], 
    'update_xml' : ['security/easylabel_group.xml', 
                    'security/ir.model.access.csv',
                    'easylabel.xml',
                    'wizard/view_wizard.xml',
                    'report/report_easylabel.xml',],
    'demo_xml' : [],
    'active' : False, 
    'installable' : True, 
}
