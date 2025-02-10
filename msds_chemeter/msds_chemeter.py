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
import logging
import shutil
import pdb
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP, float_compare)
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class ResCompany(osv.osv):
    """ Extra fields for res.company object
    """
    _inherit = 'res.company'

    _columns = {
        'msds_chemeter_folder_store': fields.char(
            'MSDS folder store', size=128,
            help="Folder for store imported PDF, default 'store' in addons "
            "root module path"),
        }

    _defaults = {
        'msds_folder_store': lambda *a: False,
        }


class MsdsChemeter(orm.Model):
    """ MSDS Form, all elements are form for product (present in more version)
    """
    _name = 'msds.chemeter'
    _description = 'MSDS Chemeter'
    _order = 'name, alias'

    def _get_file_name(self, cr, uid, product_id, context=None):
        """ Find file name for document stored
            product_id: integer single element
        """
        company_pool = self.pool.get('res.company')
        company_ids = company_pool.search(cr, uid, [], context=context)
        company = company_pool.browse(cr, uid, company_ids, context=context)[0]
        folder = os.path.expanduser(company.msds_chemeter_folder_store)
        res = os.path.join(folder, "%s.pdf" % product_id)
        return res

    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    def download_msds_form(self, cr, uid, ids, context=None):
        """ Return download file:
        """
        if context is None:
            context = {}

        attachment_pool = self.pool.get('ir.attachment')
        pallet_pool = self.pool.get('mrp.analysis.sample')

        filename = self._get_file_name(cr, uid, ids[0], context=context)
        chemeter = self.browse(cr, uid, ids, context=context)[0]
        if not os.path.isfile(filename):
            pdb.set_trace()
            # Generate filename from Chemeter call:
            ctx = context.copy()

            ctx['report_mode'] = 'sheet'
            ctx['report_action'] = 'pdf'
            ctx['force_filename'] = filename
            ctx['sheet_parameter'] = {
                'mixture': chemeter.name,
                'alias': chemeter.alias,
                'language': chemeter.language_id.code or 'it-IT'
            }

            # Call generator of PDF file:
            pallet_pool.save_pallet_report_as_odt(cr, uid, [0], context=ctx)

        name = 'MSDS.{}.{}.{}.pdf'.format(
            chemeter.name or '',
            chemeter.alias or '',
            chemeter.language_id.code or '_',
        )
        return attachment_pool.return_file_apache_php(
            cr, uid, filename, name=name, context=context)

    '''
    Label print:
    def button_msds(self, cr, uid, ids, context=None):
        """ Open MSDS
        """
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['report_mode'] = 'label'
        ctx['report_action'] = 'pdf'

        return self.save_pallet_report_as_odt(cr, uid, ids, context=ctx)

    def button_msds_print(self, cr, uid, ids, context=None):
        """ Open MSDS
        """
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['report_mode'] = 'label'
        ctx['report_action'] = 'print'

        return self.save_pallet_report_as_odt(cr, uid, ids, context=ctx)

    def open_msds_form(self, cr, uid, ids, context=None):
        """ Return a link element for use agent and open document from file
            system of MSDS form, ex.:
            openerp://msds/id.pdf
        """
        version_pool = self.pool.get('msds.form.version')
        version_ids = version_pool.search(cr, uid, [
            ('msds_id', '=', ids[0])], context=context)
        return version_pool.open_msds_form(
            cr, uid, version_ids, context=context)
    '''

    def search_product_from_mixture_domain(self, cr, uid, ids, context=None):
        """ UTILITY: Search product_ids from mixture
        """
        product_pool = self.pool.get('product.product')

        mixture = self.browse(cr, uid, ids, context=context)[0]
        name = mixture.name

        product_ids = product_pool.search(cr, uid, [
            '|',
            ('force_mixture', '=', name),
            ('default_code', '=ilike', name),
        ], context=context)

        if not product_ids and name.endswith('_'):
            # Force not present, search exactly the code without _
            product_ids = product_pool.search(cr, uid, [
                ('default_code', '=', name[:-1]),
            ], context=context)

        if not product_ids:
            raise osv.except_osv(
                'Attenzione:',
                'Non trovati prodotti con mixture: {}'.format(name))
        return product_ids

    def search_sale_from_mixture_domain(self, cr, uid, ids, context=None):
        """ UTILITY: Search product_ids from mixture
        """
        line_pool = self.pool.get('sale.order.line')

        mixture = self.browse(cr, uid, ids, context=context)[0]
        alias_code = mixture.alias or ''

        # Search product with mixture reference:
        product_ids = self.search_product_from_mixture_domain(
            cr, uid, ids, context=context)

        if alias_code:
            line_ids = line_pool.search(cr, uid, [
                ('product_id', '=', product_ids),
                ('name', '=', alias_code),
            ], context=context)
        else:
            # Search product line with name = product_id.name
            product_line_ids = line_pool.search(cr, uid, [
                ('product_id', '=', product_ids),
                # ('name', '=', alias_code),
            ], context=context)
            line_ids = []

            # Search only alias = product name line:
            for line in line_pool.browse(
                    cr, uid, product_line_ids, context=context):
                if line.name == line.product_id.name:
                    line_ids.append(line.id)
        return line_ids

    def search_product_from_mixture(self, cr, uid, ids, context=None):
        """ Search product with this mixture
        """
        product_ids = self.search_product_from_mixture_domain(
            cr, uid, ids, context=context)

        # model_pool = self.pool.get('ir.model.data')
        # view_id = model_pool.get_object_reference(
        #    cr, uid,
        #    'mrp_operations', 'inherit')[1]
        view_id = False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Prodotto'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_id': False,
            'res_model': 'product.product',
            'view_id': view_id,
            'views': [(view_id, 'tree'), (view_id, 'form')],
            'domain': [('id', 'in', product_ids)],
            'context': context,
            'target': 'current',
            'nodestroy': False,
            }

    def search_sale_from_mixture(self, cr, uid, ids, context=None):
        """ Search sale line with this mixture and name
        """
        line_ids = self.search_sale_from_mixture_domain(
            cr, uid, ids, context=context)
        model_pool = self.pool.get('ir.model.data')
        tree_view_id = model_pool.get_object_reference(
            cr, uid,
            'sapnaet',
            'view_sale_order_line_prepare_order_check_tree')[1]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Righe OC'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_id': False,
            'res_model': 'sale.order.line',
            'view_id': tree_view_id,
            'views': [(tree_view_id, 'tree')],
            'domain': [('id', 'in', line_ids)],
            'context': context,
            'target': 'current',
            'nodestroy': False,
        }

    def search_language_from_mixture(self, cr, uid, ids, context=None):
        """ Search sale line with this mixture, name and language
        """
        line_pool = self.pool.get('sale.order.line')

        line_ids = self.search_sale_from_mixture_domain(
            cr, uid, ids, context=context)

        mixture = self.browse(cr, uid, ids, context=context)[0]
        language_id = mixture.language_id.id

        # Add language:
        line_ids = line_pool.search(cr, uid, [
            ('id', 'in', line_ids),
            ('order_id.partner_id.msds_language_id', '=', language_id)
        ], context=context)

        model_pool = self.pool.get('ir.model.data')
        tree_view_id = model_pool.get_object_reference(
            cr, uid,
            'sapnaet',
            'view_sale_order_line_prepare_order_check_tree')[1]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Righe OC'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_id': False,
            'res_model': 'sale.order.line',
            'view_id': tree_view_id,
            'views': [(tree_view_id, 'tree')],
            'domain': [('id', 'in', line_ids)],
            'context': context,
            'target': 'current',
            'nodestroy': False,
        }

    # -------------------------------------------------------------------------
    # Scheduled action:
    # -------------------------------------------------------------------------
    def import_msds_form(self, cr, uid, context=None):
        """ Scheduled import for MSDS form Chemeter API generator
        """
        if context is None:
            context = {}

        sapnaet_pool = self.pool.get('sapnaet')
        company_pool = self.pool.get('res.company')

        # ---------------------------------------------------------------------
        # Get parameters:
        # ---------------------------------------------------------------------
        _logger.info(_('Start import PDF MSDS forms'))
        try:
            # todo better
            company_proxy = company_pool.browse(cr, uid, 1, context=context)
            msds_folder_store = os.path.expanduser(
                company_proxy.msds_folder_store)
            msds_mask = os.path.join(
                msds_folder_store,
                '{}.pdf'
            )
        except:
            log_message = _(
                'Error reading start up path (in / store), check '
                'Company form and correct!')
            _logger.error(log_message)
            return False

        # Launch report with parameter to get
        _logger.info(_('Generate report to get list of MSDS from DDT'))

        sapnaet_ids = sapnaet_pool.search(cr, uid, [], context=context)
        ctx = context.copy()
        ctx['update_record'] = True
        report_data = sapnaet_pool.button_report_msds_delivery_report(
            cr, uid, sapnaet_ids, context=ctx)

        # Check and update record data:
        _logger.info(_('Update record and creare PDF'))
        for key in report_data:
            mixture, alias, language = key
            mixture_ids = self.search(cr, uid, [
                ('name', '=', mixture),
                ('alias', '=', alias),
                ('language_id', '=', language.id),
            ], context=context)
            # todo

            if mixture_ids:
                regenerate_pdf = False
                # Update file
                mixture_id = mixture_ids[0]
                # todo raise if more than one?
            else:
                regenerate_pdf = True
                # Create new
                mixture_id = self.create(cr, uid, {
                    'name': mixture,
                    'alias': alias,
                    'language_id': language.id,
                }, context=context)

            if regenerate_pdf:
                filename = msds_mask.format(mixture_id)
                _logger.info('Generarting {}'.format(filename))
                # todo Generate PDF file

        _logger.info(_('End importation MSDS forms'))
        return True

    _columns = {
        'name': fields.char(
            'Codice Mixture', size=35,
            help="Code for this product"),
        'alias': fields.char(
            'Alias', size=50,
            help='Codice alias indicato nel documento cliente'),
        'language_id': fields.many2one(
            'msds.language', 'Lingua',
            required=True, help='Elenco lingue importate da Chemeter'),
        }

    # -------------
    # Button event:
    # -------------
    '''
    def open_msds_form(self, cr, uid, ids, context=None):
        """ Return a link element for use agent and open document from file
            system of MSDS form, ex.:
            openerp://msds/id.pdf
        """
        return {
            'type': 'ir.actions.act_url',
            'url': 'openerp://msds/%s.pdf' % ids[0],
            'target': 'new',
        }

    '''


class ProductProduct(orm.Model):
    """ Add extra info in product
    """
    _inherit = 'product.product'

    def _get_msds_chemeter_m2m(
            self, cr, uid, ids, field_names, arg=None, context=None):
        """ Extract Mixture MSDS Chemeter for product
        """
        if context is None:
            context = {}

        chemeter_pool = self.pool.get('msds.chemeter')
        res = {}
        product_id = ids[0]
        product = self.browse(cr, uid, product_id, context=context)
        force_mixture = product.force_mixture
        product_code = product.default_code or ''

        if force_mixture:
            mixture = force_mixture
        else:
            if not product_code:
                _logger.warning('No Mixture code found')
                return res

            mixture = '{}_{}'.format(
                product_code[:5],
                product_code[6:],
            )

        _logger.warning('Searching product mixures for {}'.format(mixture))

        res[product_id] = chemeter_pool.search(cr, uid, [
                ('name', '=', mixture),
                ('alias', '!=', False),
            ], context=context)
        return res

    _columns = {
        'msds_chemeter_ids': fields.function(
            _get_msds_chemeter_m2m,
            method=True,   # multi=True,
            relation='msds.chemeter', type='many2many',
            string='Schede'),
        }
