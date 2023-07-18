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
import openerp.netsvc as netsvc
import logging
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse


_logger = logging.getLogger(__name__)

# Global parameters:
parameters = False


class Parser(report_sxw.rml_parse):
    """ Parser item for report
    """
    def __init__(self, cr, uid, name, context):
        """ Setup Instance for this Object
        """
        self._cache_security = {}  # Clean every report

        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'load_parameter': self.load_parameter,
            'get_parameter': self.get_parameter,
            'get_analysis_info': self.get_analysis_info,
            'translate_static': self.translate_static,
            'get_security_loaded': self. get_security_loaded,
            'get_security_object': self.get_security_object,
            'get_datetime': self.get_datetime,
        })

    def get_datetime(self):
        """ Return correct datetime value
        """
        return str(datetime.now())[:19]


    def get_security_object(self, o):
        """ Return security data for last page
        """
        equipment = [  # List of equipment
            'eye',
            'skin',
            'hand',
            'air',
            'body',
            'foot',
        ]
        security_material = []
        security_advice = []
        security_symbol = []
        security_equipment = []
        total = 0.0
        rate = {}

        try:
            for material in o.bom_material_ids:
                product = material.product_id
                if product.security_off:  # Not required!
                    continue

                # Total management:
                if product not in rate:
                    rate[product] = 0.0
                quantity = material.quantity
                rate[product] += quantity
                total += quantity

                security_material.append(product)  # Always

                # Terms H:
                if product.term_h_ids:
                    for term in product.term_h_ids:
                        if term not in security_advice:
                            security_advice.append(term)

                # Danger symbol:
                if product.symbol_ids:
                    for symbol in product.symbol_ids:
                        if symbol not in security_symbol:
                            security_symbol.append(symbol)

                # Equipment:
                for part in equipment:
                    equipment_item = eval('product.protection_%s_id' % part)
                    if equipment_item and equipment_item \
                            not in security_equipment:
                        security_equipment.append(equipment_item)

                # Update rate:
            for product in rate:
                rate[product] /= total * 0.01

            # Sort:
            security_material.sort(key=lambda x: x.default_code)
            security_advice.sort(key=lambda x: x.name)
        except:
            pass  # No Security management

        return [
            (security_material, security_advice, rate, security_symbol,
             security_equipment)]

    def get_security_loaded(self, o):
        """ Load if not present the security table for this job
        """
        try:
            o_id = o.id
            if o_id not in self._cache_security:
                self._cache_security[o_id] = []
                # Load security data from Security component
                for material in o.bom_material_ids:
                    product = material.product_id
                    h = product.term_h_ids or ()
                    p = product.term_p_ids or ()
                    dpi = product.term_dpi_ids or ()

                    if h or p or dpi:
                        self._cache_security[o_id].append({
                            'product': product,
                            'H': '\n'.join(
                                [term.note or term.name for term in h]),
                            'P': '\n'.join(
                                [term.note or term.name for term in p]),
                            'DPI': '\n'.join(
                                [term.note or term.name for term in dpi]),
                        })

            return self._cache_security[o_id] or False
        except:  # No Security management
            return False

    def translate_static(self, term, lang):
        """ Translate static text for module
        """
        languages = {
            # 'en_US': {
            #    },
            'es_AR': {
                u'ORDINE DI PRODUZIONE': u'ORDER DE FABRICACIÓN',
                u'Ordine di lavorazione': u'Orden de Fabricación',
                u'ORDINE DI LAVORAZIONE': u'ORDER DE FABRICACIÓN',
                u'FOGLIO PRODUZIONE': u'HOJA DE PRODUCCIÓN',
                u'FOGLIO CONFEZIONAMENTO': u'HOLA DE ALMACEN',
                u'N. Partita': u'N. Partida',
                u'Prodotto': u'Producto',
                u'Impianto': u'Planta',
                u'Data': u'Fecha',
                u'Lavorazioni': u'Fecha',
                u'Cod. Dogan.': u'Cod. Dog.',
                u'Componenti': u'Componente',
                # 'KG': u'KG',
                # 'LT': u'LT',
                # 'SAC': u'SAC',
                u'Stampato': u'Impreso',
                u'Lotto': u'Lote',
                u'Variazioni': u'Modificación',
                u'Totale': u'Total',
                u'Quantità da produrre': u'Ciclos totales',
                u'Quantità prodotta': u'Cantidad Producida',
                u'Q.tà a magazzino Kg.': u'Cantidad en Almacen Kg.',
                u'Totale Kg.': u'Total Kg.',
                u'Griglia': u'Malla',
                u'Martelli': u'Martillos',
                u'Imballo': u'Tipo de envase',
                u'Analisi': u'Analisis',
                u'Operatori': u'Operador',
                u'Macchine': u'Ciclos producidos',
                u'Velocità': u'Velocidad',
                u'Note lavorazione': u'Notas',
                u'Tempo miscelaz.': u'Tiempo',
                u'Anomalie riscontrate': u'Anomalias de maquinaria',
                u'Temperatura': u'Temperatura',
                u'Note': u'Notas',
                u'Aspirazione': u'Aspiración',
                u'N. bancale': 'N. Tarima',
                u'Peso bancale': 'Peso',
                u'Campione n.': 'N. Muestra',
                u'Q.C.P.': 'Notas',
                u'Verifica bonifica': 'Verifica bonifica',
                u'Silos stoccaggio': 'Silos stoccaggio',
                u'Ora inizio': 'Ora inizio',
                u'Ora fine': 'Ora fine',
                },
            }
        if lang == 'it_IT' or lang not in languages:
            return term

        return languages[lang].get(term, term)

    def load_parameter(self, product_id, workcenter_id):
        """ Load browse object for get parameters
        """
        global parameters, parameter_loaded
        parameters = False  # reset previous value

        workcenter_pool = self.pool.get('mrp.workcenter')
        history_pool = self.pool.get('mrp.workcenter.history')
        if product_id and workcenter_id:
            # test if workcenter is a child:
            workcenter_proxy = workcenter_pool.browse(
                self.cr, self.uid, workcenter_id)
            if workcenter_proxy.parent_workcenter_id:
                workcenter_id = workcenter_proxy.parent_workcenter_id.id

            # Setup browse object
            history_ids = history_pool.search(self.cr, self.uid, [
                ('product_id', '=', product_id),
                ('workcenter_id', '=', workcenter_id)
            ])
            if history_ids:
                parameters = history_pool.browse(
                    self.cr, self.uid, history_ids)[0]
            else:
                _logger.error('Paramter Line - Product not found!')
        return

    def get_parameter(self, name):
        """ Return parameters browse obj
        """
        global parameters
        try:
            return parameters.__getattr__(name)
        except:
            return ""
        return parameters

    def get_analysis_info(self, production_id):
        """ Return specific information for customers that have this order line
        """
        production_browse = self.pool.get("mrp.production").browse(self.cr, self.uid, production_id)
        note = {}

        for line in production_browse.order_lines_ids:
            if line.partner_id and line.partner_id.analysis_required and line.partner_id.name not in note:
                note[line.partner_id.name] = line.partner_id.analysis_note if line.partner_id.analysis_note else "Analysis mandatory"

        res = ""
        for key in note:
            res += "[%s] %s\n" % (key, note[key])
        return res
