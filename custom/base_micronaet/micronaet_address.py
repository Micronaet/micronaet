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

class res_partner_address_micronaet_fields(osv.osv):
    _name='res.partner.address'
    _inherit ='res.partner.address'

    _columns = {
               'import': fields.boolean('Imported', required=False), # importet (c, s or d)
               'mexal_c': fields.char('Destinazione cliente', size=9, required=False, readonly=False),   # destination c 
               'mexal_s': fields.char('Destinazione fornitore', size=9, required=False, readonly=False), # destination s                        
    }
res_partner_address_micronaet_fields()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
