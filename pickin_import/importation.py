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
from openerp.tools.translate import _
import time

class importation_default_location(osv.osv):
    ''' List of 2 element for get defaulf in location and stock one
    '''
    _name = 'importation.default.location'
    _description = 'Default import location'
    
    def get_location(self, cr, uid, name, context = None):
        ''' Return default value of location
        '''
        location_ids=self.search(cr, uid, [('name','=',name)])        
        if location_ids:
           return self.read(cr, uid, location_ids)[0]['location_id'][0]
        return False
           
    _columns = {
        'name':fields.selection([
            ('customer','Customer'),            
            ('supplier','Supplier'),
            ('internal','Internal'), ],'Location type', select=True, readonly=False),
        'location_id':fields.many2one('stock.location', 'Location stock', required=True),
    }

class importation_purchase_order(osv.osv):
    ''' List of purchase order elements loaded
    '''
    
    _name = 'importation.purchase.order'
    _description = 'Purchase order import'
    _rec_name= 'product_id'
    
    def check_lot(self, cr, uid, product_id, partner_id, purchase_order, context=None):
        ''' Check in in database is yet loaded a product for a specific purchase order
            of a specific customer
            Return lot_id assigned if exist, else False
        '''
        try:
            # Search lot for product-partner-order:
            item_ids = self.search(cr, uid, [
                ('product_id', '=', product_id),
                ('partner_id', '=', partner_id),
                ('purchase_order', '=', purchase_order),
            ])
            if item_ids: # exist
                item_read = self.read(cr, uid, item_ids)[0]
                return item_read['lot_id'][0] # lot_id.id
            else:            
                # Search lot for product-partner (no order)
                item_ids = self.search(cr, uid, [
                    ('product_id', '=', product_id),
                    ('partner_id', '=', partner_id),
                    ('purchase_order', '=', False),
                ])
                if item_ids: # exist
                    item_read = self.read(cr, uid, item_ids)[0]
                    return item_read['lot_id'][0] # lot_id.id
                else:
                    # Search default lot for product
                    product_proxy = self.pool.get('product.product').browse(
                        cr, uid, product_id, context=context)
                    if product_proxy.default_prodlot_id:
                        return product_proxy.default_prodlot_id.id                    
        except:
            pass
        return False

    def new_lot(self, cr, uid, product_id, partner_id, purchase_order, lot_id, context=None):
        ''' Check if in the DB exits key element (product_id, partner_id, purchase_order)
            if true, assign lot_id as the last lot value
            if false, create new element
        '''
        item_ids = self.search(cr, uid, [
            ('product_id', '=', product_id),
            ('partner_id', '=', partner_id),
            ('purchase_order', '=', purchase_order),
        ])
        if item_ids: # save this lot as last
           item_modify = self.write(cr, uid, item_ids, {
               'lot_id': lot_id, }, context=context)         
        else:
           item_create = self.create(cr, uid, {
               'product_id': product_id,
               'partner_id': partner_id,
               'purchase_order': purchase_order,
               'lot_id': lot_id,
           }, context=context)
        return 
        
    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'purchase_order': fields.char('Purchase order', size=15, required=False, readonly=False, help="ID of PO that generate this pickin list"),
        'lot_id': fields.many2one('stock.production.lot', 'Lot', required=False),
    }
    _sql_constraints = [ # TODO non controlla se è vuoto il terzo!
        ('key_element_unique', 'unique(product_id,partner_id,purchase_order)', 'Key element: product, partner, order must be unique!')
    ]

class stock_picking_extra_fields(osv.osv):
    ''' Add extra information for import stock.picking
    '''
    _name = 'stock.picking'
    _inherit = 'stock.picking'
    
    _columns = {
        'import_document':fields.char('Document n.', size=18, required=False, readonly=False, help="Link to original imported document, format number/year ex.: 8015/2012"),
        'wizard_id': fields.integer('Wizard ID', help="Save wizard creazion ID for open stock.picking after importation")
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
