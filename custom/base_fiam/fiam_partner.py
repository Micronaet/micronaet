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

from osv import osv, fields

class res_partner_zone(osv.osv):
    _name = 'res.partner.zone'
    _order = 'name'
    
    _columns = {
        'name':fields.char('zona', size=64, required=True, readonly=False),
        'mexal_id': fields.integer('Mexal ID'),
        'type': fields.selection([
            ('region', 'Region'),
            ('state', 'State'),
            ('area', 'Area'),            
        ], 'Tipo', required=True),
    }
    _defaults = {
        'type': lambda *a: 'state',
    }
res_partner_zone()

class res_partner_fiam_fields(osv.osv):
    _name='res.partner'
    _inherit ='res.partner'

    def _function_statistics_invoice(self, cr, uid, ids, args, field_list, context=None):
        '''
        Calculate up or down of invoice:
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param context: A standard dictionary for contextual values
        @return: list of dictionary which contain partner id, colour
        '''
        if context is None: 
           context={}
        
        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            #import pdb; pdb.set_trace()
            if partner.invoiced_current_year == partner.invoiced_last_year:
               segno="equal"
               valore=0.0
            else:
               if partner.invoiced_last_year:
                  valore=100.0 * (partner.invoiced_current_year - partner.invoiced_last_year) / partner.invoiced_last_year
               else:
                  valore=100.0
               if partner.invoiced_current_year < partner.invoiced_last_year:
                  segno="down"
               else:
                  segno="up"
                        
            res[partner.id]={}
            res[partner.id]['invoice_trend']=segno
            res[partner.id]['invoice_trend_perc']=valore
        return res
        
    _columns = {
               'zone_id':fields.many2one('res.partner.zone', 'Zona', required=False), 
               'fido_date': fields.date('Data concessione fido'),
               'fido_ko':fields.boolean('Fido non concesso', required=False),
               'fido_total': fields.float('Totale fido', digits=(16, 2)),
               'mexal_note': fields.text('Mexal Note'),
               'import': fields.char('ID import', size=10, required=False, readonly=False),  # DELETE ??
               'mexal_c': fields.char('Mexal cliente', size=9, required=False, readonly=False),
               'mexal_s': fields.char('Mexal fornitore', size=9, required=False, readonly=False),                         
               'fiscal_id_code': fields.char('Fiscal code', size=16, required=False, readonly=False),  
               'private': fields.boolean('Private', required=False),               # Private (not company)
               'type_cei': fields.char('Type CEI', size=1, required=False, readonly=False),  # Type of firm (CEE, Extra CEE, Intra CEE)
               'discount_value': fields.float('Discount value', digits=(16, 2)),
               'discount_rates':fields.char('Discount scale', size=30, required=False, readonly=False),         
               # Statistics values:
               'date_last_ddt': fields.datetime('Date last DDT'),
               'day_left_ddt': fields.integer('Day left last DDT'),               
               'invoiced_current_year': fields.float('Current invoiced', digits=(16, 2)),
               'invoiced_last_year': fields.float('Last invoiced', digits=(16, 2)),
               'order_current_year': fields.float('Current order', digits=(16, 2)),
               'order_last_year': fields.float('Last order', digits=(16, 2)),            
               'invoice_trend': fields.function(_function_statistics_invoice, method=True, type='selection', selection=[
                          ('down','<'),
                          ('equal','='),
                          ('up','>'),
                          ], string='Invoice status', store=True, readonly=True, multi='invoice_stat'),   
               'invoice_trend_perc': fields.function(_function_statistics_invoice, method=True, type='float', 
                     digits=(16,2), string='Invoice diff. %', store=True, readonly=True, multi='invoice_stat'),                  
               'type_id': fields.many2one('crm.case.resource.type', 'Campaign', ), # Aggiungo il riferimento alla campagna che l'ha fatto acq.
                }
res_partner_fiam_fields()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
