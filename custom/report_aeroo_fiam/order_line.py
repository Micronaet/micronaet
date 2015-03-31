##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
# Modified template model from:
#
# Micronaet s.r.l. - Nicola Riolini
# Using the same term of use
##############################################################################

from osv import osv, fields

class product_product_extra(osv.osv):
    """
    product.product extra fields
    """
    _inherit = 'product.product'
    _name = 'product.product'
    
    _columns = {
        'telaio':fields.char('Telaio', size=64, required=False, readonly=False, translate=True),
        'pipe_diameter':fields.char('Diam. tubo', size=15, required=False, readonly=False),
        'weight_packaging':fields.char('Peso imballo', size=20, required=False, readonly=False),
        'item_per_box':fields.char('Pezzi per scatola', size=20, required=False, readonly=False),
        'item_per_pallet':fields.char('Pezzi per bancale', size=20, required=False, readonly=False),
        'item_per_mq':fields.char('Pezzi per metro cubo', size=20, required=False, readonly=False),
        'item_per_camion':fields.char('Pezzi per camion 13,6 mt.', size=20, required=False, readonly=False),

        'extra_description':fields.text('Extra description', translate=True),

        # Non visibili attualmente nella vista
        'dim_article':fields.char('Dim. art.', size=20, required=False, readonly=False),
        'dim_pack':fields.char('Dim. scatola', size=20, required=False, readonly=False),
        'dim_pallet':fields.char('Dim. pallet', size=20, required=False, readonly=False),
    }
product_product_extra()

class sale_order_extra(osv.osv):
    """
    sale.order extra fields
    """
    _inherit = 'sale.order'
    _name = 'sale.order'
    
    _columns = {
        'quotation_model':fields.selection([(1,'Offerta dettagliata (q.-sconto-subtotali)'),
                                            (2,'Offerta breve (solo q.)'),],'Model', readonly=False, required=True),
    }
    _defaults = {
        'quotation_model': lambda *x: 2, # short
    }
    
sale_order_extra()

class sale_order_line_add_fields(osv.osv):
    _name='sale.order.line'
    _inherit='sale.order.line'
    
    _columns={
             'insert_photo': fields.boolean('Con foto', required=False, help="Spuntare quando e' richiesto l'inserimento della foto a preventivo."),             
             'repeat_header_line': fields.boolean('Intest.', required=False, help="Spuntare quando e' richiesta l'intestazione, tipo dopo una riga titolo."),             
             'use_amazon_description': fields.boolean('Amazon description', required=False, help="Take amazon description instead of product's one"),
             'show_notes': fields.boolean('Show notes', required=False, help="Show notes after description"),    
             }
sale_order_line_add_fields()

