# -*- encoding: utf-8 -*-
################################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>)
#
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
################################################################################
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
################################################################################

from openerp.osv import osv, fields


# WIZARD PRINT REPORT ##########################################################
class bom_compare_wizard(osv.osv_memory):
    """ Parameter for bom report
    """

    _name = 'etl.bom.line.wizard'
    _description = 'BOM report wizard'

    # Button events:
    def print_report(self, cr, uid, ids, context=None):
        """ Redirect to bom report passing parameters
        """
        wiz_proxy = self.browse(cr, uid, ids)[0]

        datas = {}
        if wiz_proxy.all:
            datas['primary'] = False
        else:
            datas['primary'] = wiz_proxy.parent

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'webkitbomline',
            'datas': datas,
        }

    _columns = {
        'all': fields.boolean('All', required=False),
        'parent': fields.char(
            'Parent code', size=40, required=False, readonly=False),
        }

    _defaults = {
        'all': lambda *a: True,
        }


bom_compare_wizard()
