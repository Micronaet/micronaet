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

from osv import osv, fields

class res_partner_micronaet_fields(osv.osv):
    _name='res.partner'
    _inherit ='res.partner'

    _columns = {
               'import': fields.char('ID import', size=10, required=False, readonly=False),  # DELETE ??
               'mexal_c': fields.char('Mexal cliente', size=9, required=False, readonly=False),
               'mexal_s': fields.char('Mexal fornitore', size=9, required=False, readonly=False),                         
               'fiscal_id_code': fields.char('Fiscal code', size=16, required=False, readonly=False),  
               'private': fields.boolean('Private', required=False),               # Private (not company)
               'type_cei': fields.char('Type CEI', size=1, required=False, readonly=False),  # Type of firm (CEE, Extra CEE, Intra CEE)
                }
res_partner_micronaet_fields()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
