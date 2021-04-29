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
import time
from openerp.report import report_sxw
from openerp.osv import osv

# global value:
current_bom = {}
current_model = {}
rows = []
cols = []
translate_name = {}
product_note = {}
totals = {}


class report_webkit_html(report_sxw.rml_parse):
    zero = '0.0000000'

    def prepare_for_print(self, value):
        """ Format quantity value
        """
        return '%5.7f' % value

    def __init__(self, cr, uid, name, context):
        super(report_webkit_html, self).__init__(cr, uid, name,
            context=context)
        self.localcontext.update({
            'time': time,
            'cr': cr,
            'uid': uid,
            'object_list': self._object_list,
            'create_current_bom': self._create_current_bom,
            'get_current_bom': self._get_current_bom,
            'get_mp_name': self._get_mp_name,
            'get_internal_note': self._get_internal_note,
            'test_bom_model': self._test_bom_model,
            'get_cols': self._get_cols,
            'get_rows': self._get_rows,
            'get_total_cols': self._get_total_cols,
            })

    def _object_list(self,data=None):
        """ Master function that generate the list of record to print:
            row = component (all list)
            column = version of BOM
            data = row-column element for quantity (highlight also difference
                   between master bom (more or less)
        """
        global translate_name
        parent_list = []
        if data is None:
            data = {}

        domain = [('is_primary', '=', True)]
        primary = data.get('primary', False)

        if primary:
            domain.append(
                ('primary', 'ilike', primary),
                )

        parent_pool = self.pool.get('etl.bom.line')
        parent_ids = parent_pool.search(self.cr, self.uid, domain)
        parent_proxy = parent_pool.browse(self.cr, self.uid, parent_ids)

        for item in parent_proxy:
            # Description
            if item.primary not in translate_name:
                translate_name[item.primary] = item.name

            # Code for loop
            if item.primary not in parent_list:
                parent_list.append(item.primary)

        parent_list.sort()
        return parent_list

    def _create_current_bom(self, primary):
        """ Current bom, selected with primary code
        """
        global current_bom    # for save all table
        global current_model
        global cols
        global rows
        global translate_name
        global product_note
        global totals

        # initialize (every primary block is reset )
        current_bom = {}
        totals = {}
        rows = []
        cols = []

        # 1. Search lines that have passed primary name: ######################
        bom_pool = self.pool.get('etl.bom.line')
        bom_ids = bom_pool.search(self.cr, self.uid, [
            ('primary', '=', primary)
            ], order='is_primary,code,seq')  # (only version)
        bom_proxy = bom_pool.browse(self.cr, self.uid, bom_ids)

        # 2. Loop element searching: component, version
        for item in bom_proxy:  # MP name
            if item.code not in cols:  # BOM Version name
                cols.append(item.code)
                if item.code not in translate_name:
                    translate_name[item.code] = item.name
                if item.code not in product_note:
                    product_note[item.code] = item.internal_note

            # 3. Create table according to cols and rows ######################
            current_bom[(item.component_code, item.code)] = item.quantity

            # 4. Total for version (test is 1 in report) ######################
            if item.code in totals:
                totals[item.code] += item.quantity
            else:
                totals[item.code] = item.quantity

            # 5. Create model dict ############################################
            if item.is_primary:
                # '%5.5f'%(item.quantity or 0.0)
                current_model[item.component_code] = item.quantity or 0.0
            else:
                current_model[item.component_code] = 0.0

        # 6. Row list for sort:
        bom_ids = bom_pool.search(self.cr, self.uid, [
            '|',
            ('code', '=', primary),
            ('primary', '=', primary),
            ], order='primary,code,seq')  # (only version)
        bom_proxy = bom_pool.browse(self.cr, self.uid, bom_ids)
        for item in bom_proxy:
            if item.component_code not in rows:
                # for keep model first (only for previous if check)
                rows.append(item.component_code)
                if item.component_name not in translate_name:
                    translate_name[item.component_code] = item.component_name
        cols.sort()
        return True

    def _get_mp_name(self, code):
        """ Return name of component searching the code
        """
        global translate_name  # for save all table

        return translate_name.get(code, '')

    def _get_internal_note(self, code):
        """ Return name of internal note searching the code
        """
        global product_note  # for save all table

        return product_note.get(code, '')

    def _get_current_bom_real(self, row, col):
        """ Get current bom table loaded with _create_current_bom (real number)
        """
        global current_bom # for save all table
        return current_bom.get((row,col), 0.0)

    def _get_current_bom(self,row,col):
        """ Get current bom table loaded with _create_current_bom (for print)
        """
        global current_bom # for save all table

        res = self._get_current_bom_real(row,col)
        if not res:
            return '-'
        return self.prepare_for_print(res)

    def _test_bom_model(self, component_code, version_code):
        """ Test if the component code in the model loaded comparing with
            quantity passed, return :
            + Value > model
            - value < model
            > not present in model
            < not present in version
        """
        global current_model

        version = self._get_current_bom_real(component_code, version_code)
        model = current_model.get(component_code, 0.0)

        if not model and not version:
            return '='            # both zero

        if not model:             # only version
            return '>'

        if not version:           # only model
            return '<'

        if model > version:       # version less
            return '-'
        elif model == version:    # version equal not zero
            return '='
        else:                     # version more
            return '+'

    def _get_cols(self):
        """ Get current cols list loaded with _create_current_bom
        """
        global cols
        return cols

    def _get_total_cols(self, version):
        """ Return total for bom version (column)
        """
        global totals
        return self.prepare_for_print(totals.get(version, 0.0),)

    def _get_rows(self):
        """ Get current rows list loaded with _create_current_bom
        """
        global rows
        return rows


report_sxw.report_sxw(
    'report.webkitbomline',
    'etl.bom.line',
    'addons/bom_compare/report/bom_webkit.mako',
    parser=report_webkit_html,
    )
