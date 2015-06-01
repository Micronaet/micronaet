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
from openerp import tools

class res_partner_extra(osv.osv):
    ''' Extra fields
    '''
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
        'combine_name': fields.char('Dogane code (commercial)', size=30, required=False),
        'combine_name_internal': fields.char('Dogane code (internal)', size=30, required=False),
    }

class mrp_production_extra(osv.osv):
    ''' Extra fields
    '''
    _name = 'mrp.production'
    _inherit = 'mrp.production'

    # object button function:
    def get_via_number(self, cr, uid, ids, context = None):
        ''' If not present yet get sequence for VIA number and assign to this
            document
        '''
        production_proxy = self.browse(cr,uid,ids)[0]
        if not production_proxy.via_number:
           via = self.pool.get('ir.sequence').get(cr, uid, 'product.coal')
           modify = self.write(cr, uid, ids, {'via_number': via,}, context=context)
        return True 
        
    _columns = {
        'via_number': fields.char('VIA number', size=20, help="Set if there's coal material, used to print VIA document", required=False),
    }

class stock_location_type(osv.osv):
    ''' List for location used for get Coal journal movement:
        (filter only coal products)
        Commercial Journal:
        + in to internal
        - internal to out
        - internat to production
        
        Internal Journal:
        +/- internal to production
    '''
    
    _name = 'stock.location.type'
    _description = 'Stock Location type'
    _order = 'name'
    
    _columns = {
        'name': fields.selection([ ('internal','Internal location'),
                                   ('in','In location'),
                                   ('out','Out location'),
                                   ('production','Production location'),
                                   ],'Type of location', select=True, required=True, readonly=False),
        'location_id':fields.many2one('stock.location', 'Location stock', required=True),
    }
    _defaults = {
    }

class product_product_add_fields(osv.osv):
    ''' Add field to product for coal manage
    '''
    
    _name = 'product.product'
    _inherit = 'product.product'

    _columns = {
        'is_coal': fields.boolean('Is Coal', help='Check this if the product is for coal tax esention', required=False), 
        'combine_name': fields.char('Combine name', size=30, required=False),
        'combine_name_description': fields.char('Description for exempt.', size=40, required=False),
        'coal_type': fields.selection([('A','A'),('B','B'),('C','C'),('D','D'),('E','E'),],'Coal type', select=True, readonly=False, help="Col name/position in internal report"),
        'default_prodlot_id': fields.many2one('stock.production.lot', 'Default Lot', required=False),
    }

class stock_move_add_fields(osv.osv):
    ''' Add field to stock move for coal manage
    '''
    
    _name = 'stock.move'
    _inherit = 'stock.move'

    _columns = {
        'is_coal': fields.related('product_id','is_coal', type='boolean', string='Is coal', store=False),
        'via_hygro': fields.float('% Hygro VIA', digits=(5, 2), help="Hygro value in % for the movement (used for move in and move to production)"),        
        'via_number': fields.char('VIA number', size=20, help="Generated automatically by counter (in BF or BP)", required=False),
    }

class stock_picking_xab_fields(osv.osv):
    ''' Add field to stock picking for coal manage
    '''
    
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    _columns = {
        'xab_number': fields.char('XAB number', size=20, help="Set if there's a sold for coal material, XAB document printed", required=False),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
