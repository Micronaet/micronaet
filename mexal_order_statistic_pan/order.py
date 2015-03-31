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

class statistic_category(osv.osv):
    _name = 'statistic.category'
    _description = 'Categoria statistica'
    _columns = {
        'name':fields.char('Description', size=64, required=False, readonly=False),
        'trend':fields.boolean('Trend', required=False),
    }    
    _defaults = {
        'trend': lambda *a: False,
    }
statistic_category()

class res_partner_extra_fields(osv.osv):
    """
    res_partner_extra_fields
    """
    
    _inherit = 'res.partner'
    _name = 'res.partner'
    
    _columns = {
        'trend':fields.boolean('Trend', help='Insert in trend statistic, used for get only interesting partner in statistic graph',required=False),

        'statistic_category_id':fields.many2one('statistic.category', 'Categoria statistica', help='Valore di categoria statistica acquisito dal gestionale', required=False),
        'trend_category': fields.related('statistic_category_id','trend', type='boolean', string='Categoria trend', help='Indica se la gategoria viene rappresentata nel grafico del trend'),

        'saldo_c': fields.float('Saldo cliente', digits=(16, 2)),
        'saldo_s': fields.float('Saldo fornitore', digits=(16, 2)),

        'ddt_e_oc_c': fields.float('Saldo cliente OC+DDT aperti', digits=(16, 2)),
        'ddt_e_oc_s': fields.float('Saldo fornitore OC+DDT aperti', digits=(16, 2)),
    }
res_partner_extra_fields()

class statistic_header(osv.osv):
    _name = 'statistic.header'
statistic_header()

class statistic_order(osv.osv):
    '''Object that contain all order header coming from accounting
       This is only for statistic view or graph
    '''
    _name = 'statistic.order'
    _description = 'Statistic order'
    
    _order='code' #'deadline, name'

    _columns = {
        'name':fields.char('Description', size=64, required=False, readonly=False),
        #'calendar_description': fields.function(_function_calculate_lines_details, method=True, type='char', size=100, string='Total lines', store=False,),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'property_account_position': fields.related('partner_id', 'property_account_position', type='many2one', relation='account.fiscal.position', store=True, string='Fiscal position'),
        'date': fields.date('Date'),
        'deadline': fields.date('Scadenza'),
        'total': fields.float('Total', digits=(16, 2)),
        'country_id': fields.related('partner_id', 'country', type='many2one', relation='res.country', string='Country', store=True),
        # Parte delle righe dettaglio:
        'code':fields.char('Code', size=24, required=False, readonly=False),
        'quantity': fields.float('Quantity', digits=(16, 2)),
        # Parte calcolata da visualizzare per prodotto:
        'note':fields.char('Note', size=64, required=False, readonly=False),
        
        'header_id':fields.many2one('statistic.header', 'Dettagli', required=False),
        }
statistic_order()

class statistic_header_inherit(osv.osv):
    _name = 'statistic.header'
    _inherit = 'statistic.header'

    _order='deadline, name'
    _description = 'Testate ordini'

    
    _columns = {
        'name':fields.char('Numero ordine', size=16, required=False, readonly=False),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'date': fields.date('Date'),
        'deadline': fields.date('Scadenza'),
        'total': fields.float('Total', digits=(16, 2)), # TODO calcolato
        'note':fields.char('Note', size=64, required=False, readonly=False),        
        
        'property_account_position': fields.related('partner_id', 'property_account_position', type='many2one', relation='account.fiscal.position', store=True, string='Fiscal position'),
        'country_id': fields.related('partner_id', 'country', type='many2one', relation='res.country', string='Country', store=True),
        
        'line_ids':fields.one2many('statistic.order', 'header_id', 'Linee dettaglio', required=False),
    }
statistic_header_inherit()



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
        'percentage': fields.float('% sul fatt. corrente', digits=(16, 5)),
        'percentage_last': fields.float('% sul fatt. anno -1', digits=(16, 5)),
        'percentage_last_last': fields.float('% sul fatt. anno -2', digits=(16, 5)),
        'total': fields.float('Totale anno attuale', digits=(16, 2)),
        'total_last': fields.float('Totale anno -1', digits=(16, 2)),        
        'total_last_last': fields.float('Totale anno -2', digits=(16, 2)),        

        'trend_category': fields.related('partner_id', 'trend_category', type='boolean', readonly=True, string='Categoria trend'),
        'statistic_category_id': fields.related('partner_id', 'statistic_category_id', type='many2one', relation="statistic.category", readonly=True, string='Categoria statistica partner'),
        'trend': fields.related('partner_id', 'trend', type='boolean', readonly=True, string='Important partner'),

        'type_document':fields.selection([('ft','Fattura'),
                                          ('oc','Ordine'),
                                          ('bc','DDT'),
                                         ],'Tipo doc.', select=True),

        'best': fields.function(_function_index_increment, method=True, type='float', string='Best trend', multi='indici', store=True,),
        'worst': fields.function(_function_index_increment, method=True, type='float', string='Worst trend', multi='indici', store=True,),
    }
statistic_trend()

class statistic_trendoc(osv.osv):
    '''Creato stesso oggetto che conterrà pero il fatturato e gli ordini in 
       scadenza per il mese
    '''
    _inherit = 'statistic.trend'
    _name = 'statistic.trendoc'
statistic_trendoc()

class statistic_invoice(osv.osv):
    _name = 'statistic.invoice'
    _description = 'Statistic invoice'
    _order = 'month, name'
    
    _columns = {
        'name':fields.char('Descrizione', size=64, required=False, readonly=False),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'total': fields.float('Anno attuale', digits=(16, 2)),
        'total_last': fields.float('Anno -1', digits=(16, 2)),        
        'total_last_last': fields.float('Anno -2', digits=(16, 2)),        
        'type_document':fields.selection([('ft','Fattura'),
                                          ('oc','Ordine'),
                                          ('bc','DDT'),
                                         ],'Tipo doc.', select=True),
        'month':fields.selection([
            (0,'00 Non trovato'),
            (1,'01 Gennaio'),
            (2,'02 Febbraio'),
            (3,'03 Marzo'),
            (4,'04 Aprile'),
            (5,'05 Maggio'),
            (6,'06 Giugno'),
            (7,'07 Luglio'),
            (8,'08 Agosto'),
            (9,'09 Settembre'),
            (10,'10 Ottobre'),
            (11,'11 Novembre'),            
            (12,'12 Dicembre'),            
        ],'Mese', select=True, readonly=False),  
        'trend': fields.related('partner_id', 'trend', type='boolean', readonly=True, string='Important partner'),
        #'best': fields.function(_function_index_increment, method=True, type='float', string='Best trend', multi='indici', store=True,),
        #'worst': fields.function(_function_index_increment, method=True, type='float', string='Worst trend', multi='indici', store=True,),
    }
    _defaults = {
        'total': lambda *a: 0.0,
        'total_last': lambda *a: 0.0,
        'total_last_last': lambda *a: 0.0,
    }
statistic_invoice()

class statistic_invoice_product(osv.osv):
    _name = 'statistic.invoice.product'
    _description = 'Statistic invoice'
    _order = 'month, name'
    
    _columns = {
        'name':fields.char('Famiglia prodotto', size=64, required=False, readonly=False),        
        'total': fields.float('Anno attuale', digits=(16, 2)),
        'total_last': fields.float('Anno -1', digits=(16, 2)),        
        'total_last_last': fields.float('Anno -2', digits=(16, 2)),        
        'type_document':fields.selection([('ft','Fattura'),
                                          ('oc','Ordine'),
                                          ('bc','DDT'),
                                         ],'Tipo doc.', select=True),        
        'month':fields.selection([
            (0,'00 Non trovato'),
            (1,'01 Gennaio'),
            (2,'02 Febbraio'),
            (3,'03 Marzo'),
            (4,'04 Aprile'),
            (5,'05 Maggio'),
            (6,'06 Giugno'),
            (7,'07 Luglio'),
            (8,'08 Agosto'),
            (9,'09 Settembre'),
            (10,'10 Ottobre'),
            (11,'11 Novembre'),            
            (12,'12 Dicembre'),            
        ],'Mese', select=True, readonly=False),  
    }
    _defaults = {
        'total': lambda *a: 0.0,
        'total_last': lambda *a: 0.0,
        'total_last_last': lambda *a: 0.0,
    }
statistic_invoice_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
