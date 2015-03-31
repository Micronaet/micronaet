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

class sale_order_line_extra_fields(osv.osv):
    _name='sale.order.line'
    _inherit ='sale.order.line'

    _columns = {
               'price_comment': fields.text('Price comment'),
    }
sale_order_line_extra_fields()

class product_pricelist_pan_fields(osv.osv):
    _name='product.pricelist'
    _inherit ='product.pricelist'

    _columns = {
               #'import': fields.boolean('Imported', required=False), 
               'mexal_id': fields.char('Mexal Pricelist', size=9, required=False, readonly=False),  # Mexal pricelist ID
    }
product_pricelist_pan_fields()

class product_pricelist_version_pan_fields(osv.osv):
    _name='product.pricelist.version'
    _inherit ='product.pricelist.version'

    _columns = {
               #'import': fields.boolean('Imported', required=False), 
               'mexal_id': fields.char('Mexal Pricelist version', size=9, required=False, readonly=False),  # Mexal version ID
    }
product_pricelist_version_pan_fields()

class product_pricelist_item_pan_fields(osv.osv):
    _name='product.pricelist.item'
    _inherit ='product.pricelist.item'

    _columns = {
               'mexal_id': fields.char('Mexal Pricelist item', size=9, required=False, readonly=False),  # Mexal version ID
    }
product_pricelist_item_pan_fields()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
