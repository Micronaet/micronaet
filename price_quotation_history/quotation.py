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
from openerp.osv import osv, fields


#TODO Non utilizzato!!! Togliere?
class pricelist_partner_analysis(osv.osv):
    _name = 'product.partner.analysis'
    _description = 'Pricelist analysis'
    _order = 'sequence, name'
    
    _columns = {
        'name':fields.char('Descrizione analisi', size = 64, required = False, readonly = False),
        'sequence': fields.integer('Sequenza'),
        'pricelist_id':fields.many2one('product.pricelist', 'Listino', required = True),
        'partner_id':fields.many2one('res.partner', 'Partner', required = True),
        'note': fields.text('Note'),
    }

class sale_order_line(osv.osv):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'
    
    _columns = {
        'note': fields.text('Note'),
        'state': fields.related('order_id', 'state', type='selection', 
            string='Order state',
            selection=[
                ('draft', 'Draft Quotation'),
                ('sent', 'Quotation Sent'),
                ('cancel', 'Cancelled'),
                ('confirmed', 'Confirmed'),
                ('waiting_date', 'Waiting Schedule'),
                ('progress', 'Sales Order'),
                ('manual', 'Sale to Invoice'),
                ('invoice_except', 'Invoice Exception'),
                ('done', 'Done'),
                ]),
        }

class res_partner_inherit(osv.osv):
    """ Add extra fields to partner object
    """
    _name='res.partner'
    _inherit = 'res.partner'
    
    _columns = {
        #'pricelist_analysis_ids':fields.one2many('product.partner.analysis', 'partner_id', 'Listini di comparazione', help="Elenco dei listini che vengono utilizzati per comparare il prezzo durante la preventivazione", required=False),
        'pricelist_model_id':fields.many2one(
            'product.pricelist', 
            'Listino di paragone', 
            help = "Listino di paragone per avere un raffronto con il prezzo attuale del prodotto", 
            required = False),
        'pricelist_model_history_id':fields.many2one(
            'product.pricelist', 
            'Listino di riferimento', 
            help = "Listino di riferimento applicato nel caso mancassero degli articoli nel listino di base (usato per avere un raffronto nel caso esistessero particolarità",
            required = False),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
