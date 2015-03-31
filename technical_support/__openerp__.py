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
    'name' : 'Technical Support',
    'version' : '0.0.1',
    'category' : 'CRM/Support',
    'description' : """
                    Manage issue for technical company:
                    1) load issue (via mail or via form)
                       issue as a WF for status
                       add document for attivation
                    2) manage comunications for issue
                       (out with poweremail module
                        in with techmail linked to issue)
                    3) manage intervention report (use other Micronaet module)
                       every problems can generate many intervention
                       every intervention can link to many problems
                    4) backoffice: 
                       list of comunications
                       highlight old issue
                       statistic and report for customers                          
                    """,
    'author' : 'Micronaet s.r.l.',
    'website' : 'http://www.micronaet.it',
    'depends' : ['base',
                 'intervention_report',
                 'document',
                 'poweremail',
                 'fetchmail',
                ],
    'init_xml' : [], 
    'update_xml' : [
                    'security/ir.model.access.csv',                     
                    'support_views.xml',
                    'support_dashboard.xml',
                    'support_workflow.xml',
                   ],
    'demo_xml' : [],
    'active' : False, 
    'installable' : True, 
}
