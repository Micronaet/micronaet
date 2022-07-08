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


class product_product(osv.osv):
    _name='product.product'
    _inherit ='product.product'

    def _product_has_bom(sefl, cr, uid, product_id):
        '''Test if product has a bom with bom_id=false
        '''
        cr.execute("SELECT id FROM mrp_bom WHERE product_id=%s and bom_id is null", (product_id, ))
        list_bom=cr.fetchall()
        if list_bom:
           return list_bom[0][0] # return id TODO (only one?)
        else:
           return False

    def _compute_recursive_price_bom(self, cr, uid, bom_id):
        '''Recursive function for calculate bom price:
           get id of mrp.bom
           loop on child recursive with id
           return only when bom record is a leave
        '''
        # 1. find bom
        bom_proxy = self.pool.get('mrp.bom').browse(cr, uid, bom_id)

        # 2. loop on component, test if product has bom without bom_id (semi-worked)
        tot = 0
        for component in bom_proxy.bom_lines:
            has_bom = self._product_has_bom(cr, uid, component.product_id.id)
            if has_bom: # recurse:
                tot += component.product_qty * self._compute_recursive_price_bom(cr, uid, has_bom)
            else:
               if component.product_id.force_manual:
                   tot += component.product_qty * (component.product_id.manual_price or 0)   # TODO raise error?
               else:
                   tot += component.product_qty * (component.product_id.standard_price or 0) # TODO raise error?
        return tot

    def compute_price_from_bom(self, cr, uid, context=None):
        '''Procedura per calcolare il prezzo dei prodotti finiti in base
           al prezzo delle materie prime e della ricetta nella distinta
           base, viene chiamato all'esterno appena finita l'importazione
           dei prodotti e ricette
        '''
        cr.execute("SELECT id, product_id FROM mrp_bom WHERE bom_id is null")

        for item in cr.fetchall(): # loop for all bom without parent
            product_price = self._compute_recursive_price_bom(cr, uid, item[0])
            self.pool.get("product.product").write(
                cr,
                uid,
                item[1],
                {'standard_price': product_price, },
                context=context)
        return True

    def compute_price_from_bom_action(self, cr, uid, ids, context=None):
        '''Button event clicked from product.product form
        '''

        self.compute_price_from_bom(cr, uid, context=context)
        #raise osv.except_osv("Info", "Prezzi dei prodotti aggiornati!") # return??
        return True

    _columns = {
        'force_manual': fields.boolean('Force manual', required=False),
        'manual_price': fields.float('Manual price', digits=(8,5), required=True,),
    }

    _defaults = {
        'force_manual': lambda *x: False,
        'manual_price': lambda *x: 0.0,
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
