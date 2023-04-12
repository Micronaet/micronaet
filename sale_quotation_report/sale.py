# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) and the
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#    ########################################################################
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

from openerp.osv import fields,osv
from openerp.tools.translate import _


class sale_order_override(osv.osv):
    """ Change some thing in sale order for use this report
        Add some extra fields for this quotation document
    """
    _name = 'sale.order'
    _inherit = 'sale.order'

    # Override function that print order
    def print_quotation(self, cr, uid, ids, context=None):
        """
        Note: same at the original except for report_name returned
        This function prints the sales order and mark it as sent, so that we
        can see more easily the next step of the workflow
        """
        result = super(sale_order_override, self).print_quotation(
            cr, uid, ids, context=context)

        datas=result.get('datas', {})
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'crm_quotation_report',
            'datas': datas,
            'nodestroy': True}

    _columns = {
         'deadline_order': fields.date('Scadenza', required=False, readonly=False, select=True,),
         'footer_annotation_text':fields.char('Annotazione piè pagina', size=64, required=False, readonly=False),
    }

sale_order_override()

class sale_order_line_override(osv.osv):
    """ Change some thing in sale order for use this report
        Add some extra fields for this quotation document
    """
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'

    _columns = {
         'footer_annotation':fields.boolean('Nota', required=False, help="Se spuntata mette l'asterisco sul prodotto e attiva la nota a piè pagina"),
    }
sale_order_line_override()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
