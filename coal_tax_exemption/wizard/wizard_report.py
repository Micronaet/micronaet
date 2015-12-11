# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#############################################################################
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
from openerp.osv import osv, fields
from datetime import datetime


class coal_wizard_report(osv.osv_memory):
    ''' Wizard to print report
    '''
    _name = 'coal.wizard.report'
    _description = 'Coal wizard report'

    # Wizard action button:
    def print_report(self, cr, uid, ids, context=None):
        ''' Call correct report passing parameters in wizard
        ''' 
        wiz_proxy = self.browse(cr, uid, ids)[0]

        datas = {}
        datas['from_date'] = wiz_proxy.from_date
        datas['to_date'] = wiz_proxy.to_date
        datas['start'] = wiz_proxy.start
        datas['year'] = wiz_proxy.year
        datas['debug'] = wiz_proxy.debug
        datas['ids'] = []
        
        if wiz_proxy.name == 'commercial':
            report_name = 'commercial_report'
            datas['model'] = "stock.move"
            
        elif wiz_proxy.name == 'internal':    
            report_name = 'internal_report'
            datas['model'] = "stock.move"
            
        elif wiz_proxy.name == 'viap':    
            report_name = 'via_report'
            datas['model'] = "mrp.production"

        elif wiz_proxy.name == 'viain':    
            report_name = 'via_bf_report'
            datas['model'] = "stock.picking"
            
        # else not possibile    

        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas,
        }
    
    _columns = {
        'name': fields.selection([
            ('commercial', 'Commercial report'),
            ('internal', 'Internal report'),
            ('viap', 'VIA production'),
            ('viain', 'VIA in'),], 'Report name', required=True),
        'from_date': fields.date('From date'),
        'to_date': fields.date('From date'),
        'year': fields.char('Year', size=4, required = True),
        'start': fields.integer(
            'Start number',
            help="Start number for enumerate lines, passed because depend on last element write in registry"),
        'debug': fields.boolean('Debug', required=False),
    }
    
    _defaults = {
        'start': lambda *a: 1,
        'name': lambda *a: 'commercial',
        'year': lambda *a: datetime.now().strftime("%Y"),
        'debug': lambda *x: False
        
    }
coal_wizard_report()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
