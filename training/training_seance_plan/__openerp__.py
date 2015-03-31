# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu>). All Rights Reserved
#    Copyright (C) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#    Copyright (C) 2010 Micronaet S.R.L. (<http://www.micronaet.it>). All Rights Reserved
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
############################################################################################

{
    'name' : 'Training Management Seance',
    'version' : '0.1',
    'author' : 'Micronaet s.r.l.',
    'website' : 'http://www.micronaet.it',
    'category' : 'Enterprise Specific Modules/Training',
    'description' : """
          Module for update seance management, the idea is to create for every offer/session a 
          standard weekly calendar used for generate all course's seances (jumping holiday day)
          from start to end of the session. The creation of calendar is according with 
          courses of the session/offer
          """,
    'depends' : ['base',  
                 'training',
                 'base_contact',
                 'base_laser',
                 'report_aeroo',
                ],
    'init_xml' : [],
    'demo_xml' : [],
    'update_xml' : [
                    'security/ir.model.access.csv',
                    'training_seance_plan.xml',
                    'view_anag.xml',
                  	'report/report_status_seance.xml',  
                   ],
    'active' : False,
    'installable' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
