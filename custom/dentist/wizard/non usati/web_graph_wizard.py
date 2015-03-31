# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009  Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2010  Luis Falcon
#    Copyright (C) 2011-2012  Nicola Riolini - Micronaet s.r.l.
#    d$
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

from osv import fields, osv
import wizard

def _launch_wizard(self, cr, uid, data, context=None):
    """ Open PHP page with dentist plan
    """    
    if context is None:
       context = {}
    
    partner_id=data.get('id',False)
    if partner_id:   
       url="http://192.168.100.51/denti.php?partner_id=%s"%(partner_id,)
    else:
       url="http://192.168.100.51/error.php" 
       
    return {
    'type': 'ir.actions.act_url',
    'url': url,
    'target': 'new',
    }
        
class launch_web_graph_wizard(wizard.interface):
    states= {'init' : {'actions': [],
                       'result':{'type':'action',
                                 'action': _launch_wizard,
                                 'state':'end'}
                       }
             }
launch_web_graph_wizard('web_graph_wizard')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

