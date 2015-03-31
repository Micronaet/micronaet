# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

from osv import osv, fields

class res_partner_extra_fields(osv.osv):
    """
    res_partner_extra_fields
    """
    
    _inherit = 'res.partner'
    _name = 'res.partner'
    
    _columns = {
        'trend':fields.boolean('Trend', help='Insert in trend statistic, used for get only interesting partner in statistic graph',required=False),
    }
res_partner_extra_fields()

class statistic_order(osv.osv):
    '''Object that contain all order header coming from accounting
       This is only for statistic view or graph
    '''
    _name = 'statistic.order'
    _description = 'Statistic order'
    
    _order='deadline, name'
    _ref_name = 'calendar_description'

    def _function_calculate_lines_details(self, cr, uid, ids, field_name, arg, context = None):
        """
        Calcolo dati per vista a calendario
        """
        if context is None:
           context={}
           
        res={}   
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id]="OC:%s-Art.%s [Q.:%s %s]"%(order.name, order.code, order.quantity, order.type,)
        return res
        
    _columns = {
        'name':fields.char('Description', size=64, required=False, readonly=False),
        'calendar_description': fields.function(_function_calculate_lines_details, method=True, type='char', size=100, string='Total lines', store=False,),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'property_account_position': fields.related('partner_id', 'property_account_position', type='many2one', relation='account.fiscal.position', store=True, string='Fiscal position'),
        'date': fields.date('Date'),
        'deadline': fields.date('Dead line'),
        'total': fields.float('Total', digits=(16, 2)),
        'country_id': fields.related('partner_id', 'country', type='many2one', relation='res.country', string='Country', store=True),
        # Parte delle righe dettaglio:
        'code':fields.char('Code', size=24, required=False, readonly=False),
        'quantity': fields.float('Quantity', digits=(16, 2)),
        'quantity_ok': fields.float('Prodotti', digits=(16, 2)),
        'type':fields.selection([('b','Prodotto'),('n','Annullato'),],'Type of line', select=True,),
    }
statistic_order()

class statistic_deadline(osv.osv):
    _name = 'statistic.deadline'
    _description = 'Statistic deadline'
    
    _columns = {
        'name':fields.char('Deadline', size=64, required=False, readonly=False),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'deadline': fields.date('Dead line'),
        'total': fields.float('Total', digits=(16, 2)),
        'in': fields.float('Entrate', digits=(16, 2)),
        'out': fields.float('Uscite', digits=(16, 2)),
        'type':fields.selection([
            ('b','Bonifico'),            
            ('c','Contanti'),            
            ('r','RIBA'),            
            ('m','Rimessa diretta'),            
            ('x','Rimessa diretta X'),
            ('y','Rimessa diretta Y'),            
            ('z','Rimessa diretta Z'),            
            ('v','MAV'),            
        ],'Type', select=True, readonly=False),        
    }
statistic_deadline()

class statistic_trend(osv.osv):
    _name = 'statistic.trend'
    _description = 'Statistic Trend'
    
    def _function_index_increment(self, cr, uid, ids, field_name=None, arg=False, context=None):
        """
        Calcola il migliore e il peggiore incremento rispetto l'anno precedente
        """
        if context is None:
           context = {}
           
        result = {}
        for item in self.browse(cr, uid, ids, context=context):
            result[item.id]={}
            increment=(item.total or 0.0) - (item.total_last or 0.0)
            if increment > 0: #increment (best)
               result[item.id]['best']=increment or 0.0
               result[item.id]['worst']= 0.0
            else: # decrement (worst)    
               result[item.id]['worst']=-increment or 0.0
               result[item.id]['best']= 0.0
        return result
            
    _columns = {
        'name':fields.char('Description', size=64, required=False, readonly=False),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'total': fields.float('Total', digits=(16, 2)),
        'total_last': fields.float('Total year-1', digits=(16, 2)),        
        'trend': fields.related('partner_id', 'trend', type='boolean', readonly=True, string='Important partner'),
        'best': fields.function(_function_index_increment, method=True, type='float', string='Best trend', multi='indici', store=True,),
        'worst': fields.function(_function_index_increment, method=True, type='float', string='Worst trend', multi='indici', store=True,),
    }
statistic_trend()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
