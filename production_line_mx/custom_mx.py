#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP)
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import logging
import shutil
from openerp.osv import fields, osv, expression, orm
from openerp.tools.translate import _
import pdb

_logger = logging.getLogger(__name__)


class MrpProduction(orm.Model):
    """ Model name: MrpProduction
        Check all data present
    """

    _inherit = 'mrp.production'
    _order = 'name desc'

    def refresh_lavoration_material(self, cr, uid, ids, context=None):
        """ Refresh lavoration if present and not sync
        """
        lavoration_pool = self.pool.get('mrp.production.workcenter.line')
        current = self.browse(cr, uid, ids, context=context)[0]

        for lavoration in current.workcenter_lines:
            if lavoration.state in ('done', 'cancel'):
                _logger.error('Lavoration not refreshable, done or cancel!')
                continue
            lavoration_pool.load_materials_from_production(
                cr, uid, [lavoration.id], context=context)
        return True

    def add_new_lavoration(self, cr, uid, ids, context=None):
        """ Create new lavoration:
        """
        if context is None:
            context = {}

        context['default_production_id'] = ids[0]
        context['popup_mode'] = True

        return {
            'type': 'ir.actions.act_window',
            'name': _('Add lavoration'),
            'view_type': 'form',
            'view_mode': 'form',
            # 'res_id': 1,
            'res_model': 'mrp.production.workcenter.line',
            'view_id': False,
            'views': [(False, 'form')],
            'domain': [],
            'context': context,
            'target': 'new',
            'nodestroy': False,
            }

    def check_function_data_present(self, cr, uid, ids, context=None):
        """ Check normal data in all production
        """
        _logger.info('Checking MRP data')
        mrp_proxy = self.browse(cr, uid, ids, context=context)[0]
        error = ''

        # ---------------------------------------------------------------------
        # Product need code:
        # ---------------------------------------------------------------------
        if not mrp_proxy.product_id.default_code:
            error += _('MRP product %s without code\n') % (
                mrp_proxy.product_id.name
                )

        # ---------------------------------------------------------------------
        # Production material data:
        # ---------------------------------------------------------------------
        # Need default code, price on product, price on pedimento if present
        for material in mrp_proxy.bom_material_ids:
            product = material.product_id
            pedimento = material.pedimento_id
            default_code = product.default_code or ''

            # Raw material need code:
            if not default_code:
                error += _('Material %s without default code\n') % (
                    product.name
                    )

            if not product.standard_price:
                error += _('Material %s without price\n') % (
                    default_code or product.name,
                    )

            if pedimento and not pedimento.standard_price:
                error += _('Pedimento %s [%s] without price\n') % (
                    pedimento.name,
                    default_code,
                    )

        # ---------------------------------------------------------------------
        # Job material data:
        # ---------------------------------------------------------------------
        # All job need:
        #    Material code, price on product, price on pedimento if present
        for lavoration in mrp_proxy.workcenter_lines:
            for material in mrp_proxy.bom_material_ids:
                product = material.product_id
                pedimento = material.pedimento_id
                default_code = product.default_code or ''

                # Raw material need code:
                if not default_code:
                    error += _('[%s] Material %s without code\n') % (
                        lavoration.name,
                        product.name,
                        )

                if not product.standard_price:
                    error += _('[%s] Material %s without price\n') % (
                        lavoration.name,
                        default_code or product.name,
                        )

                if pedimento and not pedimento.standard_price:
                    error += _('[%s] Pedimento %s [%s] without price\n') % (
                        lavoration.name,
                        pedimento.name,
                        default_code,
                        )

        # ---------------------------------------------------------------------
        # Load data for unload material:
        # ---------------------------------------------------------------------
        for load in mrp_proxy.load_ids:
            # -----------------------------------------------------------------
            # 1. Package:
            # -----------------------------------------------------------------
            package = load.package_id.linked_product_id
            if not package.default_code:
                error += _('[%s] Load package %s without code\n') % (
                    load.sequence,
                    package.name,
                    )
            if not package.standard_price:
                error += _('[%s] Load package %s without price\n') % (
                    load.sequence,
                    package.default_code or package.name or '',
                    )

            # -----------------------------------------------------------------
            # 2. Pedimento (mandatory on package)
            # -----------------------------------------------------------------
            pedimento = load.package_pedimento_id # XXX name always present:
            if not pedimento.standard_price:
                error += _('[%s] Load pedimento [%s] %s without price\n') % (
                    load.sequence,
                    package.default_code or package.name,
                    pedimento.name,
                    )

            # -----------------------------------------------------------------
            # 3. Pallet
            # -----------------------------------------------------------------
            pallet = load.pallet_product_id
            if pallet and not pallet.default_code:
                error += _('[%s] Load pallet %s without code\n') % (
                    load.sequence,
                    pallet.name,
                    )
            if pallet and not pallet.standard_price:
                error += _('[%s] Load pallet %s without price\n') % (
                    load.sequence,
                    pallet.default_code or pallet.name or '',
                    )
        # print error
        return self.write(cr, uid, ids, {
            'check_mrp': error,
            }, context=context)

    # Override to check product name
    def load_materials_from_bom(self, cr, uid, ids, context=None):
        """ Override original action
        """
        # Call normally:
        super(MrpProduction, self).load_materials_from_bom(
            cr, uid, ids, context=context)
        return self.check_function_data_present(
            cr, uid, ids, context=context)

    _columns = {
        'check_mrp': fields.text('Check error'),
        'mode': fields.selection([
            ('production', 'Real Production'),
            ('waste', 'Waste product'),
            ], 'Mode'),
        }

    _defaults = {
        'mode': lambda *x: 'production',
        }


class MrpProductionWorkcenterLoad(orm.Model):
    """ Model name: Mrp Production Workcenter Load
        Add extra fields for waste management:
    """

    _inherit = 'mrp.production.workcenter.load'

    _columns = {
        'waste_id': fields.many2one(
            'product.product', 'Waste product',
            help='When there\'s some waste production this product is loaded'),
        'waste_qty': fields.float('Waste Qty', digits=(16, 2)),
        }


class MrpProductionMaterial(orm.Model):
    """ Model name: Material pedimento
    """

    _inherit = 'mrp.production.material'

    def dummy_button(self, cr, uid, ids, context=None):
        """ Dummy button
        """
        return True

    def manage_pedimento_error(self, cr, uid, ids, context=None):
        """ Duplicate line for use remain qty with another pedimento
        """
        material = self.browse(cr, uid, ids, context=context)[0]

        qty = material.quantity
        pedimento_qty = material.pedimento_id.product_qty

        if qty <= pedimento_qty:
            raise osv.except_osv(
                _('Error'),
                _('Split not necessary, request %s, pedimento %s') % (
                    qty, pedimento_qty),
                )

        # Use pedimento qty for this line
        self.write(cr, uid, ids, {
            'quantity': pedimento_qty,
            }, context=context)

        # Create remain line:
        self.create(cr, uid, {
            'mrp_production_id': material.mrp_production_id.id,
            'quantity': qty - pedimento_qty,
            'product_id': material.product_id.id,
            'standard_price': material.standard_price,
            'pedimento_id': False,  # Let choose to the user!
            }, context=context)

        # Refresh view:
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            }

    def _get_pedimento_covered(self, cr, uid, ids, fields, args, context=None):
        """ Fields function for calculate
        """
        res = {}
        for material in self.browse(cr, uid, ids, context=context):
            qty = material.quantity
            if material.pedimento_id:
                pedimento_qty = material.pedimento_id.product_qty
                res[material.id] = (qty <= pedimento_qty)
            else:
                res[material.id] = True  # till selection
        return res

    def _get_accounting_covered(
            self, cr, uid, ids, fields, args, context=None):
        """ Fields function for calculate waste
        """
        res = {}
        for material in self.browse(cr, uid, ids, context=context):
            qty = material.quantity
            accounting_qty = material.accounting_qty
            res[material.id] = (qty <= accounting_qty)
        return res

    _columns = {
        'pedimento_id': fields.many2one(
            'product.product.pedimento', 'Pedimento'),
        'standard_price': fields.related(
            'product_id', 'standard_price',
            type='float', string='Standard price'),
        'pedimento_price': fields.related(
            'pedimento_id', 'standard_price',
            type='float', string='Pedimento price'),
        'pedimento_covered': fields.function(
            _get_pedimento_covered, method=True,
            type='boolean', string='Pedimento covered'),
        'accounting_covered': fields.function(
            _get_accounting_covered, method=True,
            type='boolean', string='Pedimento covered'),
        }


class product_product_extra(osv.osv):
    """ Extra fields for product.product object
    """
    _inherit = "product.product"

    def rpc_import_stock_status_mx(
            self, cr, uid, stock, context=None):
        """ Launched externally (store procedure and passed database)

            -------------------------------------------------------
            |                     Read parameters:                |
            -------------------------------------------------------
            |PEDIMENTO: dbo.sp_existence_Pedimento_Product (col 9)|
            |STANDARD:  dbo.sp_existence_Product           (col 6)|
            -------------------------------------------------------
            |       Field             | PEDIMENTO   |  STANDARD   |
            | Code                    |     0       |      0      |
            | Name                    |     1       |      1      |
            | Type: MP                |     2       |      3      |
            | Control:                |     3       |      2      |
            |     pediment, unit, lot |             |             |
            | Pediment                |     4       |             |
            | Lot                     |     5       |             |
            | Existence               |     6       |      4      |
            | Cost                    |     7       |             |
            | Last cost               |     8       |      5      |
            -------------------------------------------------------
        """
        _logger.info('Import stock status from external')

        if not stock:
            _logger.error('Cannot import, no stock and pedimento stock passed')
            return False

        # ---------------------------------------------------------------------
        #                          PEDIMENTO MANAGEMENT:
        # ---------------------------------------------------------------------
        mail_pool = self.pool.get('mail.thread')
        pedimento_pool = self.pool.get('product.product.pedimento')
        _logger.info('Reset stock for pedimentos if present')
        pedimento_ids = pedimento_pool.search(cr, uid, [], context=context)
        pedimento_pool.write(
            cr, uid, pedimento_ids, {
                'product_qty': 0.0,
                }, context=context)

        # ---------------------------------------------------------------------
        # Import pedimento and stock:
        # ---------------------------------------------------------------------
        multi_lot_total = {}
        check_double = {}
        double = []
        total = {}
        product_type_db = []
        for row in stock:
            if len(row) == 6:  # unit col 6
                # -------------------------------------------------------------
                continue  # XXX Not used for now:
                default_code = row[0]
                name = row[1]
                control = row[2] # unit
                product_type = row[3] # MP
                pedimento = False
                lot = False
                product_qty = row[4]
                cost = 0.0
                last_cost = row[5]
                # -------------------------------------------------------------

            else:  # pedimento: col 9
                default_code = row[0]
                name = row[1]
                product_type = row[2]  # MP
                control = row[3]  # pedimento
                pedimento = row[4]
                lot = row[5]
                product_qty = row[6]
                cost = row[7]
                last_cost = row[8] or cost

                if lot:  # so no pedimento!
                    pedimento = lot  # Use pedimento as a code
                    pedimento_code = lot  # Use lot for code
                else:
                    pedimento_code = pedimento.replace(' ', '')  # clean

            if control == 'pediment':
                control = 'pedimento'

            # -----------------------------------------------------------------
            # Mandatory fields check:
            # -----------------------------------------------------------------
            if not default_code:
                _logger.error('%s. Code empty (jump line)' % row)
                continue

            product_ids = self.search(cr, uid, [
                ('default_code', '=', default_code),
                ], context=context)
            if not product_ids:
                _logger.error(
                    '%s. Code not found in ODOO %s (jump line)' % (
                        row, default_code))
                continue
            product_id = product_ids[0]

            # -----------------------------------------------------------------
            # Product type:
            # -----------------------------------------------------------------
            product_type_db.append((product_id, product_type))

            # -----------------------------------------------------------------
            # Total update:
            # -----------------------------------------------------------------
            if product_id not in total:
                total[product_id] = [0, last_cost, control]
            total[product_id][0] += product_qty

            # -----------------------------------------------------------------
            # Pedimento / Lot (use same management):
            # -----------------------------------------------------------------
            # Pedimento present
            # if pedimento:
            key = (pedimento_code, product_id)
            if key not in check_double:
                check_double[key] = product_qty
            else:
                check_double[key] += product_qty  # used to get total q.
                if control == 'pedimento':  # lot could be double!
                    double.append((default_code, pedimento))  # for log double
            subtotal = check_double[key]

            # Search now:
            odoo_ids = pedimento_pool.search(cr, uid, [
                ('code', '=', pedimento_code),
                ('product_id', '=', product_id),
                ], context=context)
            if odoo_ids:  # Update pedimento:
                data = {
                    'product_qty': subtotal,  # total for all read!
                    }
                if last_cost:  # XXX Update only if present:
                    data['standard_price'] = last_cost
                pedimento_pool.write(
                    cr, uid, [odoo_ids[0]], data,
                    context=context)
            else:  # Create pedimento:
                pedimento_pool.create(cr, uid, {
                    'name': pedimento,
                    'code': pedimento_code,
                    'product_id': product_id,
                    'product_qty': subtotal,
                    'standard_price': last_cost,
                    }, context=context)

        # ---------------------------------------------------------------------
        # Update product type:
        # ---------------------------------------------------------------------
        for product_id, product_type in product_type_db:
            try:
                self.write(cr, uid, [product_id], {
                    'product_type': product_type,
                    }, context=context)
            except:
                _logger.error(
                    '%s product type not found: MP, PT' % product_type)
                continue

        # ---------------------------------------------------------------------
        # Reset accounting qty in ODOO:
        # ---------------------------------------------------------------------
        _logger.info('Update product total:')
        product_ids = self.search(cr, uid, [
            ('accounting_qty', '!=', 0),
            ], context=context)
        self.write(cr, uid, product_ids, {
            'accounting_qty': 0.0,
            }, context=context)

        for product_id in total:
            product_qty, last_cost, control = total[product_id]
            if control == 'lotandpediment':
                control = 'pediment'

            # -----------------------------------------------------------------
            # Update product data:
            # -----------------------------------------------------------------
            data = {
                'accounting_qty': product_qty,
                'product_mode': control,
                }
            if last_cost > 0.001:
                data['standard_price'] = last_cost

            self.write(
                cr, uid, product_id, data, context=context)
        _logger.info('End import product account status')

        if double:
            query = 'select partner_id from res_users;'
            cr.execute(query)
            partner_ids = [item[0] for item in cr.fetchall()]
            double_text = ''
            for item in double:
                double_text += 'Codice: %s, Prodotto: %s\n' % item
            mail_pool.message_post(
                cr, uid, False,
                type='email',
                body='Trovati numeri pedimento doppi in Contipaq: %s' % (
                    double_text, ),
                subject='Trovati doppioni',
                partner_ids=[(6, 0, partner_ids)],
                context=context)
        return True

    # -------------------------------------------------------------------------
    #                               Scheduled actions
    # -------------------------------------------------------------------------
    def schedule_etl_product_state_mx(
            self, cr, uid, path=False, start=1, context=None):
        """ Import from Import Excel file from accounting
        """
        return True
        # TODO remove, called from external:

    def get_waste_product(self, cr, uid, ids, context=None):
        """ Update if present same product with R
        """
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        default_code = current_proxy.default_code or ''
        waste_code = 'R' + default_code[1:]  # Same as code but used R* format
        product_ids = self.search(cr, uid, [
            ('default_code', '=', waste_code),
            ], context=context)
        if product_ids:
            return self.write(cr, uid, ids, {
                'waste_ids': product_ids[0],
                }, context=context)
        else:
            raise osv.except_osv(
                _('Waste code'),
                _('Product %s doesn\'t have waste code: %s' % (
                    default_code,
                    waste_code,
                    )),
                )

    _columns = {
        'waste_id': fields.many2one(
            'product.product', 'Waste product',
            help='When there\'s some waste production this product is loaded'),
        'forced_price': fields.float(
            'Forced price', digits=(16, 3),
            help='Force price for raw material in product price'),
        }


class MrpProductionWorkcenterLineExtra(osv.osv):
    """ Update some _defaults value
    """
    _inherit = 'mrp.production.workcenter.line'

    def dummy_button(self, cr, uid, ids, context=None):
        """ Dummy button
        """
        return True

    # Override for manage pedimento
    # >>> ORM Function:
    def create(self, cr, uid, vals, context=None):
        """ Override create method only to generate BOM materials in subfield
            bom_materials_ids, initially is a copy of mrp.production ones
        """
        mrp_pool = self.pool.get('mrp.production')
        material_pool = self.pool.get('mrp.production.material')

        vals['real_date_planned_end'] = self.add_hour(
            vals.get('real_date_planned',False),
            vals.get('hour',False))
        if vals.get('force_cycle_default', False):
            res = self.cycle_historyzation(cr, uid, vals, context=context)
            vals['force_cycle_default'] = False
            # after historization force return False

        res_id = super(MrpProductionWorkcenterLineExtra, self).create(
            cr, uid, vals, context=context)
        if res_id:  # Create bom for this lavoration: (only during creations)!!
            # TODO test if is it is not created (or block qty if present)?
            mrp_proxy = mrp_pool.browse(
                cr, uid, [vals.get('production_id', 0)], context=context)[0]
            total = mrp_proxy.product_qty

            # Delete previous procedure records:
            material_ids = material_pool.search(cr, uid, [
                ('workcenter_production_id', '=', res_id),
                ], context=context)
            material_pool.unlink(cr, uid, material_ids, context=context)

            for item in mrp_proxy.bom_material_ids:
                # proportionally created on total production order
                # and total job order
                item_id = material_pool.create(cr, uid, {
                    'product_id': item.product_id.id,
                    'quantity': item.quantity * vals.get(
                        'product_qty', 0.0) / total if total else 0.0,
                    # current yet created WC line:
                    'workcenter_production_id': res_id,
                    'pedimento_id': item.pedimento_id.id or False,
                    }, context=context)
        return res_id

    def _create_bom_lines(
            self, cr, uid, lavoration_id, from_production=False,
            context=None):
        """ Create a BOM list for the passed job
            Actual items will be deleted and reloaded with quantity passed
        """
        lavoration_browse = self.browse(
            cr, uid, lavoration_id, context=context)
        try:
            mrp = lavoration_browse.production_id
            bom = mrp.bom_id
            if not bom and not lavoration_browse.product_qty:
                return False  # TODO raise error

            # Delete all elements:
            material_pool = self.pool.get('mrp.production.material')
            material_ids = material_pool.search(cr, uid, [
                ('workcenter_production_id', '=', lavoration_id),
                ], context=context)
            material_pool.unlink(cr, uid, material_ids, context=context)

            # Create elements from bom:
            if from_production:
                for element in mrp.bom_material_ids:
                    material_pool.create(cr, uid, {
                        'product_id': element.product_id.id,
                        'quantity':
                            element.quantity / mrp.product_qty *
                            lavoration_browse.product_qty
                            if mrp.product_qty else 0.0,
                        'pedimento_id': element.pedimento_id.id,
                        'uom_id': element.product_id.uom_id.id,
                        'workcenter_production_id': lavoration_id,
                    }, context=context)
            else:
                for element in bom.bom_lines:
                    material_pool.create(cr, uid, {
                        'product_id': element.product_id.id,
                        'quantity':
                            element.product_qty *
                            lavoration_browse.product_qty / bom.product_qty
                            if bom.product_qty else 0.0,
                        'pedimento_id': False,
                        'uom_id': element.product_id.uom_id.id,
                        'workcenter_production_id': lavoration_id,
                    }, context=context)
            return True
        except:
            return False

    # -------------------------------------------------------------------------
    # Schedule import log:
    # -------------------------------------------------------------------------
    def schedule_import_log_event(self, cr, uid, folder, context=None):
        """ Start import from folder:
        """
        def clean(value):
            """ Clean as ascii
            """
            res = ''
            for c in (value or ''):
                if ord(c) < 127:
                    res += c
                else:
                    res += '*'
            return res

        path = os.path.expanduser(folder)
        _logger.info('Start reading log path: %s' % path)

        wc_db = {}
        move_file = []
        for root, folders, files in os.walk(path):
            for f in files:
                if not f.startswith('load_') and not f.startswith('unload_'):
                    _logger.error('Jump file in incorrect format: %s' % f)
                    continue  # no correct format

                # -------------------------------------------------------------
                # Extract data from filename:
                # -------------------------------------------------------------
                part = f.split('.')
                openerp_part = part[0].split('_')
                account_part = part[1].split('-')

                mode = openerp_part[0]
                wc_id = int(openerp_part[1])
                account_ref = account_part[1]
                account_date = account_part[2]

                if wc_id not in wc_db:
                    wc_db[wc_id] = {}  # data to create after log read

                # Write file name read:
                wc_db[wc_id].update({
                    'log_filename_%s' % mode: f,
                    'log_account_%s' % mode: account_ref,
                    'log_account_date_%s' % mode: account_date,
                    })

                # -------------------------------------------------------------
                # Read file:
                # -------------------------------------------------------------
                fullname = os.path.join(path, f)
                history_name = os.path.join(path, 'history', f)
                move_file.append((fullname, history_name))

                log_error = False
                log_error_text = ''
                log_detail = ''

                i = 0
                for line in open(fullname, 'r'):
                    i += 1
                    if i == 1:
                        continue  # Jump header

                    line.strip()
                    if not line:
                        continue

                    # Fixed file:
                    control = line[:24].strip()
                    note = line[24:64].strip()  # 'Inserted movement' # CORRECT
                    error = line[64:120].strip()
                    default_code = line[120:144].strip()
                    qty = line[144:160].strip()
                    uom = line[160:168].strip()
                    cost = line[168:176].strip()
                    pedimento = line[176:198].strip()
                    lot = line[198:216].strip()
                    stock = line[216:217].strip()

                    # CSV file:
                    # row = line.split('\t')
                    # control = row[0].strip()
                    # note = row[1].strip() # 'Inserted movement' # CORRECT
                    # error = row[2].strip()
                    # default_code = row[3].strip()
                    # qty = row[4].strip()
                    # uom = row[5].strip()
                    # cost = row[6].strip()
                    # lot = row[7].strip() # or pedimento

                    # Update data:
                    if note != 'Inserted movement':
                        log_error = True
                        log_error_text += clean(line)
                    log_detail += clean(line)

                wc_db[wc_id].update({
                    'log_error_%s' % mode: log_error,
                    'log_error_text_%s' % mode: log_error_text,
                    'log_detail_%s' % mode: log_detail,
                    })
            break  # only first folder

        # Update database with log files:
        _logger.info('Update log info in database:')
        for wc_id in wc_db:
            try:
                self.write(cr, uid, [wc_id], wc_db[wc_id], context=context)
            except:
                _logger.info('Workcenter ID %s no more present!' % wc_id)

        # TODO remove only if update database!
        # History file read (after modify database):
        _logger.info('History file read:')
        for from_file, to_file in move_file:
            _logger.info('Move file: %s  >>  %s' % (from_file, to_file))
            shutil.move(from_file, to_file)
        return True

    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    def mark_ok(self, cr, uid, ids, context=None):
        """ Mark as view the log error
        """
        return self.write(cr, uid, ids, {
            'log_ok': True,
            }, context=context)

    _columns = {
        # Unload block:
        'log_filename_unload': fields.char('Filename unload', size=64),
        'log_error_unload': fields.boolean('Error state unload'),
        'log_error_text_unload': fields.text('Error text unload'),
        'log_detail_unload': fields.text('Detail unload'),
        'log_account_unload': fields.char('Account unload ID', size=20),
        'log_account_date_unload': fields.char('Account date load', size=20),

        # Load block:
        'log_filename_load': fields.char('Filename load', size=64),
        'log_error_load': fields.boolean('Error state load'),
        'log_error_text_load': fields.text('Error text load'),
        'log_detail_load': fields.text('Detail load'),
        'log_account_load': fields.char('Account load ID', size=20),
        'log_account_date_load': fields.char('Account date load', size=20),

        'log_ok': fields.boolean('OK (unload and load)'),
       }
