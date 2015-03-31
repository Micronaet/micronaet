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
    'name' : 'HR Resource Planning',
    'version' : '1.0.1',
    'category' : 'HR/Customization',
    'description' : """Module for planning human resource:
                       Generate a calendar for set up work month
                       for all employees  
                       Get some tools for control cover of activity 
                       (something like: from 8 to 16, Mon to Wed, I need 3 cleaner)
                       Depends on presence badge box, get timesheet automatically
                    """,
    'author' : 'Micronaet s.r.l.',
    'website' : 'http://www.micronaet.it',
    'depends' : ['base','hr','hr_timesheet',],
    'init_xml' : [], 
    'update_xml' : [
                    'security/ir.model.access.csv',
                    'planning.xml',
                    'wizard/planning_wizard.xml',],
    'demo_xml' : [],
    'active' : False, 
    'installable' : True, 
}
