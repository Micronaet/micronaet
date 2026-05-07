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
import urllib
import re
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP, float_compare)
from openerp.tools.translate import _


# Utility:
def clean_windows_filename(filename):
    """ Remove not allowed characters for Windows file name
        Remove not ASCII char
    """
    not_admit = r'[<>:"/\\|?*\x00-\x1F]'
    filename = re.sub(not_admit, '-', filename)
    filename = filename.rstrip('. ')  # No extra space or .
    result = ''
    for c in filename:
        if ord(c) > 127:
            result += '-'
        else:
            result += c

    # nomi_riservati = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7',
    #                  'COM8', 'COM9',
    #                  'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
    # nome_base, estensione = re.match(r'^(.*?)(?:\.([^.]+))?$', nome_file_pulito).groups()
    # if nome_base.upper() in nomi_riservati:
    #    nome_base = "_" + nome_base
    # nome_file_pulito = nome_base + (("." + estensione) if estensione else "")

    # 4. Limita la lunghezza del nome del file (opzionale)
    # lunghezza_massima = 255
    # nome_file_pulito = nome_file_pulito[:lunghezza_massima]
    # alias.encode('utf-8', 'replace').decode('utf-8')
    return result


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


class ResCountry(osv.osv):
    """ Extra field in country
    """
    _inherit = 'res.country'

    def schedule_update_msds_language(self, cr, uid, context=None):
        """ Update partner lang depend on language
        """
        country_ids = self.search(cr, uid, [
            ('msds_language_id', '!=', False),
        ], context=context)
        for item_id in country_ids:
            self.msds_language_update(cr, uid, [item_id], context=context)
        return True

    def msds_language_update(self, cr, uid, ids, context=None):
        """ update language to partner of this country
        """
        partner_pool = self.pool.get('res.partner')
        country = self.browse(cr, uid, ids[0], context=context)

        msds_language_id = country.msds_language_id.id
        if not msds_language_id:
            return False

        partner_ids = partner_pool.search(cr, uid, [
            ('sql_customer_code', '!=', False),
            ('msds_language_manual', '=', False),
            ('country_id', '=', country.id),
            ('msds_language_id', '!=', msds_language_id),
        ], context=context)

        _logger.warning(
            u'Update #{} customer country: {}'.format(
                len(partner_ids), country.code))

        return partner_pool.write(cr, uid, partner_ids, {
            'msds_language_id': msds_language_id,
        }, context=context)

    _columns = {
        'msds_language_id': fields.many2one('msds.language', 'Lingua Chemeter'),
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

    # ------------------------------------------------------------------------------------------------------------------
    # Button event:
    # ------------------------------------------------------------------------------------------------------------------
    def open_msds_chemeter_form(self, cr, uid, ids, context=None):
        """ Return download file:
        """
        if context is None:
            context = {}

        attachment_pool = self.pool.get('ir.attachment')
        filename = self._get_file_name(cr, uid, ids[0], context=context)
        chemeter = self.browse(cr, uid, ids, context=context)[0]
        if not os.path.isfile(filename):
            raise osv.except_osv(
                'Attenzione:',
                'Non trovato il mixture: {}'.format(chemeter.name))
        pdf_file = open(filename, 'r')
        if pdf_file.read(4) != '%PDF':
            raise osv.except_osv(
                'Attenzione:',
                'Non è un file PDF quello salvato, rigenerarlo: '
                '{}'.format(chemeter.name))
        return attachment_pool.return_file_apache_php(
            cr, uid, filename, name='', context=context)

    def download_msds_form(self, cr, uid, ids, context=None):
        """ Return download file:
        """
        if context is None:
            context = {}

        pallet_pool = self.pool.get('mrp.analysis.sample')
        filename = self._get_file_name(cr, uid, ids[0], context=context)
        try:
            os.remove(filename)
            _logger.warning('Remove {}'.format(filename))
        except:
            _logger.warning('Cannot remove {}'.format(filename))

        chemeter = self.browse(cr, uid, ids, context=context)[0]
        mixture = chemeter.name
        alias = chemeter.alias or u''
        language = chemeter.language_id.code

        # Generate filename from Chemeter call:
        ctx = context.copy()
        ctx['report_mode'] = 'sheet'
        ctx['report_action'] = 'pdf'

        alias = clean_windows_filename(alias)
        try:
            ctx['sheet_parameter'] = {
                'mixture': urllib.quote(mixture),
                'alias': urllib.quote(alias),
                'language': urllib.quote(language),
                # or 'it-IT'
            }
        except:
            raise osv.except_osv('Errore', u'Errore caratteri nel nome Alias non validi: {}'.format(alias))

        # Call generator of PDF file:
        reply = pallet_pool.save_pallet_report_as_odt(
            cr, uid, [0], context=ctx)
        try:
            url = reply.get('url')
            if context.get('wizard_mode'):
                return reply

            _logger.warning('Saving Chemeter MSDS as {}'.format(filename))
            command = "wget -O \"{}\" --content-disposition \"{}\"".format(
                filename, url
            )
            os.system(command)
            # todo check if is a PDF file here
        except:
            raise osv.except_osv(
                'Attenzione:',
                'Non trovato il mixture: {}'.format(mixture))
        return True

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
            msds_folder_store = os.path.expanduser(company_proxy.msds_folder_store)
            msds_mask = os.path.join(
                msds_folder_store,
                '{}.pdf',   # TODO format value?
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
        report_data = sapnaet_pool.button_report_msds_delivery_report(cr, uid, sapnaet_ids, context=ctx)

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
        'manual': fields.boolean(
            'Manuale',
            help='Creato manualmente per stampa da Wizard'),
        'name': fields.char(
            'Codice Mixture', size=35,
            help="Code for this product"),
        'alias': fields.char(
            'Alias', size=100,
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

    def rdp_get_mixture_code(self, cr, uid, ids, context=None):
        """ Extract mixture code from RPD call remote
        """
        product_id = ids[0]
        product = self.browse(cr, uid, product_id, context=context)
        return self.get_mixture_code(product)        
            
    def get_mixture_code(self, product):
        """ Extract mixture code
        """
        if product.force_mixture:
            # 1. Forced code:
            return product.force_mixture

        else:
            default_code = (product.default_code or '').upper()
            start1 = default_code[:1] or ''
            if not default_code or start1 in 'ABCLMPRVWZ' or start1.isdigit():
                # 2. No Code or Excluded items:
                _logger.warning('No Mixture code found (or excluded): {}'.format(default_code))
                return ''

            elif start1 == 'E':  # TODO M?
                # 3. used as is code, like Energo:  (TODO Machine code)
                return default_code

            # 4. Granulometry code:
            return '{}_{}'.format(default_code[:5], default_code[6:])

    def scheduled_set_all_product_mixture(self, cr, uid, context=None):
        """ Set all mixtures
        """
        # Update pattern product:
        updates = {}

        cr.execute('''
            SELECT id 
            FROM product_product 
            WHERE 
                default_code is not null AND 
                default_code != '' AND
                left(default_code, 1) not in (
                    'A', 'B', 'C', 'L', 'M', 'P', 'R', 'V', 'W', 'Z', 
                    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9');
            ''')
        product_ids = [record[0] for record in cr.fetchall()]
        _logger.info('Selected {} product to update mixture'.format(len(product_ids)))

        for product in self.browse(cr, uid, product_ids, context=context):
            new_mixture = self.get_mixture_code(product) or False
            if product.msds_mixture_code != new_mixture:
                updates.setdefault(new_mixture, []).append(product.id)

        # Update operation:
        for new_mixture in updates:
            record_ids = updates[new_mixture]
            self.write(cr, uid, record_ids, {
                'msds_mixture_code': new_mixture,
            }, context=context)
        _logger.info('Updated {} mixture product'.format(len(updates)))
        return True

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
        mixture = self.get_mixture_code(product)
        _logger.warning('Searching product mixure for {}'.format(mixture))
        res[product_id] = chemeter_pool.search(cr, uid, [
                ('name', '=', mixture),
                ('alias', '!=', False),
            ], context=context)
        return res

    _columns = {
        'msds_mixture_code': fields.char('Codice Mixture', size=35),
        'msds_manual': fields.boolean(
            'MSDS Manuale',
            help='Non permette la stampa della scheda, va fatta a mano '
                 'e poi corretta in Word'),
        'msds_chemeter_ids': fields.function(
            _get_msds_chemeter_m2m,
            method=True,   # multi=True,
            relation='msds.chemeter', type='many2many',
            string='Schede'),
        'msds_form_present': fields.boolean(
            'Scheda presente', help='Caricato il dato con una procedura automatica'),
        }
