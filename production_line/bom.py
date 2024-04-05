# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import pdb
import sys
import logging
from openerp import tools
from openerp.osv import osv, fields, orm

from datetime import datetime, timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP, float_compare)
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)


# Objects:
class BomProductAlernative(osv.osv):
    """ Alternative groups for BOM
    """
    _name = 'bom.product.alternative'

    # -------------------------------------------------------------------------
    # Utility:
    # -------------------------------------------------------------------------
    def get_alternative_groups(self, cr, uid, ids, product_id, context=None):
        """ Extract product alternatives for a product
        """
        res = False
        if not product_id:
            return res
        query = """
            SELECT DISTINCT product_id
            FROM bom_product_alternative_group_rel
            WHERE group_id in (
                SELECT group_id
                FROM bom_product_alternative_group_rel
                WHERE product_id = %s);
            """
        cr.execute(query, [product_id])
        res = [r[0] for r in cr.fetchall()]
        return res

    def choose_material_alternative(self, cr, uid, ids, context=None):
        """ Open alternatives materials
        """
        if context is None:
            context = {}

        from_id = context.get('from_id')
        from_model = context.get('from_model')
        if not from_id or not from_model:
            raise Exception('Non trovato origine per aggiornare')

        # Pool used:
        model_pool = self.pool.get('ir.model.data')
        from_pool = self.pool.get(from_model)

        view_id = model_pool.get_object_reference(
            cr, uid,
            'production_line', 'view_bom_product_alternative_list_tree')[1]

        # Get information from record/model:
        from_line = from_pool.browse(cr, uid, ids, context=context)[0]
        from_product_id = from_line.product_id.id  # For alternative
        product_ids = self.get_alternative_groups(
            cr, uid, ids, from_product_id, context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Prodotti alternativi'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': False,
            'res_model': 'product.product',
            'view_id': view_id,
            'views': [(view_id, 'tree')],
            'domain': [('id', 'in', product_ids)],
            'context': context,
            'target': 'new',
            'nodestroy': False,
            }

    _columns = {
        'name': fields.char('Nome raggruppamento', size=35, required=True),
        'group_ids': fields.many2many(
            'product.product', 'bom_product_alternative_group_rel',
            'group_id', 'product_id',
            'Prodotti'),
    }


class ProductProduct(osv.osv):
    """ Alternative groups for BOM
    """
    _inherit = 'product.product'

    def select_this_product_button(self, cr, uid, ids, context=None):
        """ Update previous DB with new product
        """
        if context is None:
            context = {}
        from_id = context.get('from_id')
        from_model = context.get('from_model')
        if not from_id or not from_model:
            raise Exception('Non trovato origine per aggiornare')

        from_pool = self.pool.get(from_model)
        return from_pool.write(cr, uid, [from_id], {
            'product_id': ids[0]}, context=context)

    _columns = {
        'concentration': fields.float(
            '% Concentrazione', digits=(5, 2),
            help='Concentrazione del prodotto, utilizzato per valutare'
                 'la quantità da utilizzare nelle ricette o per '
                 'ricalcolarla quando viene scambiato con altri prodotti.'),
    }

    _defaults = {
        'concentration': lambda *x: 100.0,
    }


class MrpBom(osv.osv):
    """ Alternative groups for BOM
    """
    _inherit = 'mrp.bom'

    def write_thread_message(
            self, cr, uid, ids, subject='', body='', context=None):
        """ Write generic message
        """
        # Default part of message:
        message = {
            'subject': subject,
            'body': body,
            'type': 'comment',  # 'notification', 'email',
            'subtype': False,   # parent_id, #attachments,
            'content_subtype': 'html',
            'partner_ids': [],
            'email_from': 'openerp@micronaet.it',  # wizard.email_from,
            'context': context,
            }
        msg_id = self.message_post(cr, uid, ids, **message)
        return

    def force_new_recipe_quantity(self, cr, uid, ids, context=None):
        """ Recalc recipe
        """
        bom = self.browse(cr, uid, ids, context=context)[0]

        original_data = []
        modify_data = {}

        message = ''  # For logging

        original_bom_qty = new_bom_qty = 0.0
        message += u'\n<b>Cambio prodotto:</b>\n'
        for line in bom.bom_lines:
            new_product = line.product_id
            org_product = line.base_product_id
            original_bom_qty += line.base_product_qty

            if new_product == org_product:   # Not touched lines:
                original_data.append(line)
                new_bom_qty += line.base_product_qty
            else:
                old_qty = line.base_product_qty
                new_concentration = \
                    line.force_concentration or new_product.concentration or \
                    100.0
                old_concentration = org_product.concentration or 100.0
                product_qty = old_qty * old_concentration / new_concentration
                message += u'%.6f x [%s conc. %.2f] a [%s conc. %.2f] = ' \
                           'nuova q. %.6f\n' % (
                                line.base_product_qty,
                                org_product.default_code,
                                old_concentration,

                                new_product.default_code,
                                new_concentration,
                                product_qty,
                                )

                # Touched lines:
                modify_data[line.id] = {
                    'product_qty': product_qty,
                    'force_concentration': new_concentration,
                }
                new_bom_qty += product_qty

        # Update modify data:
        for record_id in modify_data:
            data = modify_data[record_id]
            self.write(cr, uid, [record_id], data, context=context)

        # Update not modify data:
        k = new_bom_qty / old_qty  # Remain coeff.

        message += '\n' \
            'Totale ricetta: vecchia %.6f VS attuale %.6f = ' \
            'coeff. %.6f\n' % (
                original_bom_qty,
                new_bom_qty,
                k,
                )

        message += u'\n<b>Nuove quantità ricalcolate:</b>\n'
        for line in original_data:
            product_qty = line.base_product_qty * k
            self.write(

                cr, uid, [line.id], {
                    # Recalc with coeff:
                    'product_qty': product_qty,
                    }, context=context)
            message += '<b>%s</b> da %.6f a %.6f\n' % (
                line.base_product_id.default_code,
                line.base_product_qty,
                product_qty,
            )

        if message:
            self.write_thread_message(
                cr, uid, ids,
                subject='Ricalcolata distinta base:',
                # '<table class="oe_list_content">%s</table>',
                body=message.replace('\n', '<br/>'),
                context=context)
        return True

    def choose_material_alternative(self, cr, uid, ids, context=None):
        """ Open alternatives materials
        """
        if context is None:
            context = {}
        alternative_pool = self.pool.get('bom.product.alternative')

        ctx = context.copy()
        ctx.update({
            'from_id': ids[0],
            'from_model': 'mrp.bom',
        })
        return alternative_pool.choose_material_alternative(
            cr, uid, ids, context=ctx)

    def _function_base_data(
            self, cr, uid, ids, fields, args, context=None):
        """ Fields function for calculate
        """
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            base_product = line.base_product_id
            product = line.product_id
            if base_product:
                res[line.id] = {
                    'is_changed': base_product and base_product != product,
                    'base_concentration': base_product.concentration or 100.0,
                    'product_concentration': product.concentration or 100.0,
                }
            else:
                res[line.id] = {
                    'is_changed': False,
                    'base_concentration': 0.0,
                    'product_concentration': 0.0,
                }

        return res

    _columns = {
        'mrp_id': fields.many2one(
            'mrp.production', 'Produzione',
            help='Indica che la distinta base è stata personalizzata solo '
                 'per questa produzione (è anche stata disattivata e visibile '
                 'solo da questo collegamento nella produzione)'),
        'create_date': fields.datetime('Data creazione'),
        #  'is_active': fields.boolean('Attivo (rimuovere)!'),
        'obsolete': fields.boolean(
            'Obsoleta',
            help='Se attivo è considerata obsolete e non visibile in '
                 'produziones'),

        # Bom line:
        'base_product_id': fields.many2one(
            'product.product', 'Prod. orig.', required=False),
        'base_product_qty': fields.float(
            'Q. orig', digits=(10, 6), required=False),
        'force_concentration': fields.float(
            'Forza % concentr.', digits=(10, 2)),

        'base_concentration': fields.function(
            _function_base_data, method=True, multi=True, digits=(10, 2),
            type='float', string='% Conc. orig.', store=False),
        'product_concentration': fields.function(
            _function_base_data, method=True, multi=True, digits=(10, 2),
            type='float', string='% Conc.', store=False),
        'is_changed': fields.function(
            _function_base_data, method=True, multi=True,
            type='boolean', string='Cambiato', store=False),
    }


class MrpProduction(osv.osv):
    """ Alternative groups for BOM
    """
    _inherit = 'mrp.production'

    # -------------------------------------------------------------------------
    # Custom BOM management:
    # -------------------------------------------------------------------------
    def restore_bom_materials_for_mrp(self, cr, uid, ids, context=None):
        """ Restore original Bom for production
        """
        bom_pool = self.pool.get('mrp.bom')

        mrp_id = ids[0]
        mrp = self.browse(cr, uid, mrp_id, context=context)
        bom = mrp.bom_id
        bom_id = bom.id
        origin_bom = mrp.origin_bom_id
        if not origin_bom or bom == origin_bom or not bom.mrp_id:
            _logger.error('Distinta base già nella versione originale')
            return False

        # Update reference BOM:
        self.write(cr, uid, ids, {
            'bom_id': origin_bom.id,
            'origin_bom_id': False,
        }, context=context)

        self.write_thread_message(
            cr, uid, [mrp_id],
            subject='Ripristino distinta base originale prodotto',
            # body=body,
            context=context)

        # Remove custom BOM:
        return bom_pool.unlink(cr, uid, [bom_id], context=context)

    def load_custom_bom_materials_for_mrp(self, cr, uid, ids, context=None):
        """ Generate a custom BOM for this order
        """
        bom_pool = self.pool.get('mrp.bom')

        mrp_id = ids[0]
        mrp = self.browse(cr, uid, mrp_id, context=None)

        current_bom = mrp.bom_id
        if current_bom.mrp_id:  # Is a MRP BOM
            raise Exception(
                'La ricetta è già personalizzata, modificarla o '
                'ripristinare quella originale')

        current_bom_id = current_bom.id
        bom_name = u'%s [Pers. x %s]' % (
                current_bom.name, mrp.name)
        default_data = {
            'mrp_id': mrp_id,
            'active': False,
            'name': bom_name,
            }
        new_bom_id = bom_pool.copy(
            cr, uid, current_bom_id, context=context)
        # Update with default:
        bom_pool.write(cr, uid, [new_bom_id], default_data, context=context)

        # Update lines data:
        lines = bom_pool.browse(cr, uid, new_bom_id, context=context).bom_lines
        for line in lines:
            bom_pool.write(cr, uid, [line.id], {
                'base_product_id': line.product_id.id,
                'base_product_qty': line.product_qty,
            }, context=context)

        # Update reference BOM:
        data = {'bom_id': new_bom_id}
        if not mrp.origin_bom_id:
            data['origin_bom_id'] = mrp.bom_id.id  # Save current BOM

        self.write_thread_message(
            cr, uid, [mrp_id],
            subject='Impostata distinta base personalizzata: %s' % bom_name,
            # body=body,
            context=context)

        return self.write(cr, uid, ids, data, context=context)

    _columns = {
        'origin_bom_id': fields.many2one(
            'mrp.bom', 'Origin BOM',
            help='Origin BOM before custom'),
    }


class MrpProductionMaterial(osv.osv):
    """ Alternative groups for BOM
    """
    _inherit = 'mrp.production.material'

    def choose_material_alternative(self, cr, uid, ids, context=None):
        """ Open alternatives materials
        """
        if context is None:
            context = {}

        # Check state:
        this_line = self.browse(cr, uid, ids, context=context)[0]
        # mrp_production_id

        # Check only for WC, production can change
        if this_line.workcenter_production_id.accounting_sl_code:
            raise orm.except_orm(
                'Errore', u'Lavorazione già chiusa, non possibile cambiare')

        alternative_pool = self.pool.get('bom.product.alternative')

        ctx = context.copy()
        ctx.update({
            'from_id': ids[0],
            'from_model': 'mrp.production.material',
        })
        return alternative_pool.choose_material_alternative(
            cr, uid, ids, context=ctx)
