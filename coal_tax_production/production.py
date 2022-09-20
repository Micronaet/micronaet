# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>)
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
from datetime import datetime, timedelta
from openerp.tools.translate import _
from openerp import netsvc


class mrp_production_extra(osv.osv):
    """ Add estra fields for coal BOM
    """
    _name = 'mrp.production'
    _inherit = 'mrp.production'

    # --------
    # Utility:
    # --------
    def create_bom_coal(self, cr, uid, production_id, context=None):
        """ Create a mrp.production from bom_id passed (coal bom)
        """
        production_proxy = self.browse(cr, uid, production_id, context=context)

        if not production_proxy.coal_production_id:
            # Create a new production order (header):
            new_id = self.create(cr, uid, {
                #'name': production_proxy.name,
                'product_id': production_proxy.product_id.id,
                'product_uom': production_proxy.product_uom.id,
                'product_qty': production_proxy.product_qty,
                'prodlot_id': production_proxy.prodlot_id.id,
                'date_planned': production_proxy.date_planned,
                #'workcenter_id': production_proxy.workcenter_id.id,
                'bom_id': production_proxy.bom_id.coal_bom_id.id,
                'user_id': production_proxy.user_id.id,
            }, context=context)

            # VIA button:
            self.pool.get('mrp.production').get_via_number(cr, uid, [new_id], context=context)

            # button_confirm event:
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'mrp.production', new_id, 'button_confirm', cr)
            # Manual button_force event
            # Manual force todo from view

            # Update parent production with new linked coal production:
            self.write(cr, uid, production_id, {'coal_production_id': new_id}, context=context)
        return True

    _columns = {
        'coal_production_id':fields.many2one('mrp.production', 'Coal production',
            required=False, help="Coal BOM linked to production yet created",
            ondelete="set null"),
        'linked_to_coal': fields.boolean('Linked to coal production', required=False),
    }

    _defaults = {
        'coal_production_id': False,
        'linked_to_coal': False,
    }


class mrp_production_extra(osv.osv):
    """ Add estra fields for coal BOM
    """
    _name = 'mrp.bom'
    _inherit = 'mrp.bom'


    # -------------------
    # On Change function:
    # -------------------
    def onchange_only_coal(self, cr, uid, only_coal, context=None):
        """ Reset BOM
        """
        res = {}
        if not only_coal:
            res['value'] = {}
            res['value']['coal_bom_id'] = False
        return res

    _columns = {
        'only_coal': fields.boolean('Only for coal', required=False,
            help='Only for coal BOM, go in coal registry!'),
        'coal_bom_id':fields.many2one('mrp.bom', 'Coal BOM',
            required=False, domain=[('bom_id', '=', False)],
            help="Auto generate related bom for coal production and registry",
            ondelete="set null"),
    }
    _defaults = {
        'only_coal': False,
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
