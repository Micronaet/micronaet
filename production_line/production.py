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

class production_line(osv.osv):
    ''' Production lines for create products
    '''
    _name = 'production.line'
    _description = 'Production line'
    
    _order='code,name'

    _columns = {
        'code': fields.integer('Code', required=True),
        'name':fields.char('Line name', size=64, required=False, readonly=False),
        'note': fields.text('Note'),
        }
production_line()


class production_production_order(osv.osv):
    ''' Production order to create material on a line
    '''    
    _name = 'production.production.order'
    _description = 'Production order'

    _order='name'

    _columns = {
        'name':fields.char('Production Order ID', size=15, required=False, readonly=False), # automatic
        'date': fields.datetime('Start'),
        'duration': fields.float('Total', digits=(16, 2)),
        'product_id':fields.many2one('product.product', 'Product', required=False),
        'quantity': fields.float('Quantity', digits=(16, 2)),
        'note':fields.char('Note', size=64, required=False, readonly=False),

        # Relation fields:
        'line_id':fields.many2one('production.line', 'Line', required=True),
        }
production_production_order()
    
class production_order_line(osv.osv):
    '''Object that contain all order header coming from accounting
       This is only for statistic view or graph
    '''
    _name = 'production.customer.order.line'
    _description = 'Production order.line'
    
    _order='sequence,name'

    _columns = {
        'name':fields.char('Order ID', size=64, required=False, readonly=False),
        'sequence': fields.integer('Sequence'),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'date': fields.date('Date'),
        'deadline': fields.date('Scadenza'),
        'product_id':fields.many2one('product.product', 'Product', required=False),
        'quantity': fields.float('Quantity', digits=(16, 2)),
        'note':fields.char('Note', size=64, required=False, readonly=False),

        # Relation fields:
        'order_id':fields.many2one('production.production.order', 'Order', required=False),
        }
production_order_line()

class production_production_order(osv.osv):
    ''' Production order (for extra relation fields
    '''
    _name = 'production.production.order'
    _inherit = 'production.production.order'

    _columns = {
        # Relation fields:
        'order_line_ids':fields.one2many('production.customer.order.line', 'order_id', 'Production lines', required=False),
        }
production_production_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
