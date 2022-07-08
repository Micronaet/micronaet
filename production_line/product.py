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
import sys
import openerp.netsvc as netsvc
import logging
from openerp import tools
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from utility import no_establishment_group


_logger = logging.getLogger(__name__)


class product_packaging(osv.osv):
    """ Extra fields for product.packaging object
    """
    _name = 'product.packaging'
    _inherit = 'product.packaging'

    _columns = {
        'is_active': fields.boolean('Is Active'),
        }

    _defaults = {
        'is_active': lambda *x: True,
        }


class product_ul_extra(osv.osv):
    """ Extra fields for product.product object
    """
    _name = 'product.ul'
    _inherit = 'product.ul'

    '''def hide_product_ul(self, cr, uid, ids, context=None):
        """ Hide product UL
        """
        return self.write(cr, uid, ids, {
            'active': False,
            }, context=context)

    def show_product_ul(self, cr, uid, ids, context=None):
        """ Show product UL
        """
        return self.write(cr, uid, ids, {
            'active': True,
            }, context=context)

    '''
    # todo maybe a scheduled action (not yes scheduled):
    def import_ul(self, cr, uid, file_name_package, context=None):
        """ load accounting list of ul (from files for now)
        """
        if not file_name_package:
            return False

        filename = os.path.expanduser(file_name_package)
        for line in open(filename, 'r'):
            try:
                code = line[:10].strip()
                name = "%s [%s]" % (
                    line[10:40].strip().title(),
                    code,
                    )
                product_code = line[40:47].strip()

                linked_product_id = self.pool.get('product.product').search(
                    cr, uid, [
                        ('default_code', '=', product_code)
                    ], context=context)
                if not linked_product_id:
                    # log error
                    continue # jump line
                linked_product_id = linked_product_id[0]

                ul_id = self.search(cr, uid, [
                    ('code', '=', code)], context=context)
                data = {
                    'code': code,
                    'name': name,
                    'linked_product_id': linked_product_id,
                    'type': 'unit',
                    }
                if ul_id:
                    self.write(cr, uid, ul_id, data, context=context)
                else:
                    self.create(cr, uid, data, context=context)
            except:
                break
        return True

    _columns = {
        'product_ids': fields.one2many('product.packaging', 'ul', 'Product'),
        'code': fields.char('Code', size=10, required=False, readonly=False),
        'linked_product_id': fields.many2one(
            'product.product', 'Product linked', required=False,
            help="Used for unload package product after lavoration"),
        # 'active': fields.boolean('Attivo'),
        }

    # _defaults = {
    #    'active': lambda *x: True,
    #    }


class product_product_extra(osv.osv):
    """ Extra fields for product.product object
    """
    _inherit = 'product.product'

    def scheduled_check_product_price(self, cr, uid, ids, context=None):
        """ Check price and save last
        """
        sql_pool = self.pool.get('micronaet.accounting')
        product_pool = self.pool.get('product.product')
        user_pool = self.pool.get('res.users')

        # Parameters:
        reference = 50.0

        if self.table_capital_name(cr, uid, context=context):
            table = 'AR_ANAGRAFICHE'
        else:
            table = 'ar_anagrafiche'

        cursor = sql_pool.connect(cr, uid, year=False, context=context)
        if not cursor:
            _logger.error('Cannot read product price cursor')

        cursor.execute("""
            SELECT CKY_ART, NMP_UCA, NMP_COSTD  
            FROM %s;
            """ % table)

        records = cursor.fetchall()
        _logger.warning('Product selected from %s: %s' % (
            table, len(records),
            ))
        raise_error = []
        for record in records:
            default_code = record['CKY_ART']
            new_price = record['NMP_UCA'] or record['NMP_COSTD']

            # -----------------------------------------------------------------
            # Remove unused:
            # -----------------------------------------------------------------
            # Water and discount:
            if default_code[:2] in ('VV', ):
                _logger.warning('Code not used: %s' % default_code)
                continue
            if default_code in ('SCONTO', ):
                _logger.warning('Code not used: %s' % default_code)
                continue

            # No cost:
            if not new_price:
                _logger.warning('Cost not found %s' % default_code)
                continue

            # Not present:
            product_ids = product_pool.search(cr, uid, [
                ('default_code', '=', default_code),
            ], context=context)
            if not product_ids:
                _logger.error('Product not found %s' % default_code)
                continue

            # Warning: more than one
            if len(product_ids) > 1:
                _logger.warning(
                    'More product found %s, use first' % default_code)

            product_id = product_ids[0]
            product = product_pool.browse(cr, uid, product_id, context=context)
            last_standard_price = \
                product.last_standard_price or product.standard_price

            # Check price:
            gap = abs(last_standard_price - new_price) / new_price
            if gap > reference:
                raise_error.append(
                    (default_code, last_standard_price, new_price))

            # Update price (if needed)
            product_pool.write(cr, uid, [product_id], {
                'last_standard_price': new_price,  # Not visible in form!
                'standard_price': new_price,
                }, context=context)

        # Raise error on telegram:
        message = ''
        for record in raise_error:
            message += '%s: da %s a %s' % record

        if message:
            message = 'Segnalazione prezzi anomali:\n%s' % message
            # todo send with telegram:
            user = user_pool.browse(cr, uid, uid, context=context)
            telegram_id = user.company_id.telegram_product_id.id

            #command_send_telegram(
            #        self, cr, uid, telegram_id, message, context=None)
        return True

    # def check_price_out_of_scale(self, cr, uid, ids, context=None):

    # -------------
    # Override ORM:
    # -------------
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        """
        Return a view and fields for current model. where view will be depends on {view_type}.
        @param cr: cursor to database
        @param uid: id of current user
        @param view_id: list of fields, which required to read signatures
        @param view_type: defines a view type. it can be one of (form, tree, graph, calender, gantt, search, mdx)
        @param context: context arguments, like lang, time zone
        @param toolbar: contains a list of reports, wizards, and links related to current model

        @return: returns a dict that contains definition for fields, views, and toolbars
        """
        if view_type == 'form' and no_establishment_group(self, cr, uid, context=context):
            toolbar = False
        return super(product_product_extra, self).fields_view_get(
            cr, uid, view_id, view_type, context=context, toolbar=toolbar)

    # -------------------------------------------------------------------------
    #                               Scheduled actions
    # -------------------------------------------------------------------------
    def schedule_etl_product_state_mssql(self, cr, uid, verbose=True,
            as_dict=True, file_name_package=False, context=None):
        """ Import from MSSQL DB linked to Company AQ_QUANTITY elements
        """
        _logger.info("Start import packages list")

        # Pool used:
        ul_pool = self.pool.get('product.ul')
        accounting_pool = self.pool.get('micronaet.accounting')
        product_packaging_pool = self.pool.get('product.packaging')
        product_pool = self.pool.get("product.product")

        try:
            cursor = accounting_pool.get_product_package_columns(
                 cr, uid, context=context)
            if not cursor:
                _logger.error('Unable to connect no package imported!')

            # -----------------------------------------------------------------
            #                Import Product UL from file:
            # -----------------------------------------------------------------
            if file_name_package:
                ul_pool.import_ul(cr, uid, file_name_package, context=context)
                ul_ids = ul_pool.search(cr, uid, [], context=context)
                codepackage_2_id = {}
                for item in ul_pool.browse(cr, uid, ul_ids, context=context):
                    codepackage_2_id[item.code] = item.id

                # Get list of package with the ID
                # (used in product-package populate operations)
                for record in cursor:
                    try:
                        code = record['COLUMN_NAME'].strip()  # no "NGD_"
                        if code[:4] != "NGD_":
                            continue # jump no field NGD_

                        code = code[4:]
                        pul_id = codepackage_2_id.get(code, False)
                        if not pul_id:
                            _logger.error("UL code not found: '%s'" % code)
                    except:
                        _logger.error(sys.exc_info())

                # -------------------------------------------------------------
                # Start importation product-package:
                # -------------------------------------------------------------
                _logger.info("Start import packages for product")

                cursor = accounting_pool.get_product_package(
                    cr, uid, context=context)
                if not cursor:
                    _logger.error(
                        'Unable to connect no importation of package list '
                        'for product!')

                # loop on all product elements with package
                for product_package in cursor:
                    product_code = product_package['CKY_ART'].strip()
                    product_ids = product_pool.search(cr, uid, [
                        ('default_code', '=', product_code),
                    ], context=context)
                    if not product_ids:
                        _logger.error(
                            "Product not found, code: '%s'" % product_code)
                        continue  # next record!

                    product_id = product_ids[0]
                    # loop on all elements/columns
                    # (package NGD_* *=code of package)
                    for key in codepackage_2_id:
                        try:
                            # TODO why a False value??!?!?!?!?
                            if not key:
                                _logger.error('Key not present!')
                                continue
                            code = "NGD_" + key
                            # Q. is the value of the fields NDG_code!
                            qty = product_package.get(code, 0.0)
                            if qty > 0.0:  # search if present and > 0
                                ul = codepackage_2_id.get(key, False)
                                if not ul:
                                   _logger.error(
                                       "UL: '%s' not found (used in product: '%s')" % (
                                           key, product_code,))
                                   continue  # next record (jump this)!
                                # search if package is yet present:
                                ul_ids = product_packaging_pool.search(cr, uid, [
                                    ('product_id', '=', product_id),
                                    ('ul', '=', ul),
                                ])  # ('code','=',key)
                                if ul_ids: # modify
                                    res = product_packaging_pool.write(
                                        cr, uid, ul_ids, {'qty': qty},
                                        context=context)
                                else:      # create
                                    item_id = product_packaging_pool.create(
                                        cr, uid, {
                                            'product_id': product_id,
                                            'ul': ul,
                                            'qty': qty,
                                            }, context=context)

                        except:
                            _logger.error(sys.exc_info())
        except:
            _logger.error('Error import package during status importation!')

        # ---------------------------------------------------------------------
        # Start syncro product state:
        # ---------------------------------------------------------------------
        _logger.info('Start syncro product state')
        cursor = accounting_pool.get_product_quantity(
            cr, uid, 1, 9, context=context)  # current year always 9
        if not cursor:
            _logger.error(
                'Unable to connect no importation of product state quantity!')

        # Verbose variables:
        total = 0
        records = 0
        verbose_quantity = 100

        # todo Rewrite using base_mssql_accounting
        try:
            for record in cursor:
                try:
                    records += 1

                    default_code = record['CKY_ART'].strip()

                    item_id = self.search(cr, uid, [
                        ('default_code', '=', default_code),
                        ], context=context)
                    if item_id:
                        accounting_qty = record['NQT_INV'] + \
                            record['NQT_CAR'] - record['NQT_SCAR']
                        self.write(cr, uid, item_id, {
                            'accounting_qty': accounting_qty,
                            }, context=context)
                        total += 1

                    if verbose and (records % verbose_quantity == 0):
                        _logger.info('%s State updated: %s]!' % (
                            records, total))
                except:
                    _logger.error(
                        'ETL MSSQL: Error update product state! [%s]' % (
                            sys.exc_info()))
            _logger.info(
                'Import state terminated! %s Imported %s!' % (records, total))
        except:
            _logger.error(sys.exc_info(), )
            return False
        return True

    # Fields functions:
    def _function_linked_accounting_qty(
            self, cr, uid, ids, field, args, context=None):
        """ Calculate total of sale order line for used for accounting store
        """
        res = dict.fromkeys(ids, 0)
        sol_pool = self.pool.get('sale.order.line')
        sol_ids = sol_pool.search(cr, uid, [
            ('product_id', 'in', ids),
            ('use_accounting_qty', '=', True),
            ], context=context)
        for line in sol_pool.browse(cr, uid, sol_ids, context=context):
            try:
                res[line.product_id.id] += line.product_uom_qty or 0.0
            except:
                pass # no error!
        return res

    _columns = {
        'last_standard_price': fields.float(
            'Prezzo precedente', digits=(16, 3)),
        'accounting_qty': fields.float('Account quantity', digits=(16, 3)),
        'linked_accounting_qty': fields.function(
            _function_linked_accounting_qty, method=True, type='float',
            string='OC qty linked to store', store=False, multi=False),

        'minimum_qty': fields.float('Minimum alert quantity', digits=(16, 3)),
        'maximum_qty': fields.float('Maximum alert quantity', digits=(16, 3)),
        'not_in_status': fields.boolean('Not in status',
            help='If checked in webkit report of status doesn\'t appear'),
        # 'to_produce': fields.boolean('To produce', help='If checked this
        # product appear on list of os lines during creation of production
        # orders'),

        'is_pallet': fields.boolean('Is a pallet', help='The product is a pallet '),
        'pallet_max_weight': fields.float('Pallet weight', digits=(16, 3),
            help='Max weight of the load on this pallet'),

        'mrp_yield': fields.float('MRP m(x) yield', digits=(16, 3)),
        'mrp_waste': fields.float('MRP m(x) waste', digits=(16, 3)),
        }

    _defaults = {
        'accounting_qty': lambda *a: 0.0,
        'minimum_qty': lambda *a: 0.0,
        'not_in_status': lambda *a: False,
        'is_pallet': lambda *a: False,
        }


# ID function:
def get_partner_id(self, cr, uid, ref, context=None):
    """ Get OpenERP ID for res.partner with passed accounting reference
    """
    partner_id=self.pool.get("res.partner").search(cr, uid, ["|","|",('mexal_c','=',ref),('mexal_d','=',ref),('mexal_s','=',ref)], context=context)
    return partner_id[0] if partner_id else False


def browse_partner_id(self, cr, uid, item_id, context=None):
    """ Return browse obj for partner id
    """
    browse_ids = self.pool.get('res.partner').browse(cr, uid, [item_id], context=context)
    return browse_ids[0] if browse_ids else False


def browse_partner_ref(self, cr, uid, ref, context=None):
    """ Get OpenERP ID for res.partner with passed accounting reference
    """
    partner_id = self.pool.get("res.partner").search(cr, uid, ["|", "|", ('mexal_c', '=', ref), ('mexal_d', '=', ref),('mexal_s','=',ref)], context=context)
    return self.pool.get('res.partner').browse(cr, uid, partner_id[0], context=context) if partner_id else False


def get_product_id(self, cr, uid, ref, context=None):
    """ Get OpenERP ID for product.product with passed accounting reference
    """
    item_id = self.pool.get('product.product').search(cr, uid, [('default_code', '=', ref)], context=context)
    return item_id[0] if item_id else False

def browse_product_id(self, cr, uid, item_id, context=None):
    """ Return browse obj for product id
    """
    browse_ids = self.pool.get('product.product').browse(cr, uid, [item_id], context=context)
    return browse_ids[0] if browse_ids else False

def browse_product_ref(self, cr, uid, ref, context=None):
    """ Return browse obj for product ref
        Create a minimal product with code ref for not jump oc line creation
        (after normal sync of product will update all the fields not present
    """
    item_id = self.pool.get('product.product').search(cr, uid, [('default_code', '=', ref)], context=context)
    if not item_id:
       try:
           uom_id = self.pool.get('product.uom').search(cr, uid, [('name', '=', 'kg')],context=context)
           uom_id = uom_id[0] if uom_id else False
           item_id=self.pool.get('product.product').create(cr, uid, {
               'name': ref,
               'name_template': ref,
               'mexal_id': ref,
               'default_code': ref,
               'sale_ok': True,
               'type': 'consu',
               'standard_price': 0.0,
               'list_price': 0.0,
               'description_sale': ref,  # preserve original name (not code + name)
               'description': ref,
               'uos_id': uom_id,
               'uom_id': uom_id,
               'uom_po_id': uom_id,
               'supply_method': 'produce',
           }, context=context)
       except:
           return False  # error creating product
    else:
        item_id=item_id[0]  # first
    return self.pool.get('product.product').browse(cr, uid, item_id, context=context)
