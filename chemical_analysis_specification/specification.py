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
from openerp.osv import osv, fields
from datetime import datetime

class analysis_supplier_request(osv.osv):
    _name = 'analysis.supplier.request'
    _description = 'Analysis request'
    
    from datetime import datetime
    
    _columns = {
        'name':fields.char('Description', size=64, required=True, readonly=False),
        'date': fields.date('From date', required=True),
        'partner_id':fields.many2one('res.partner', 'Partner', required=True),
        
        'product_id':fields.many2one('product.product', 'Product', required=False),
        # Chemical references in Analysis module:
        'chemical_category_id':fields.many2one('chemical.product.category', 'Chemical Category', required=False),
        'model_id': fields.many2one('product.product.analysis.model', string='Analysis model'),   
        'note': fields.text('Note'),     
    }
    _defaults = {
        'date': lambda *a: datetime.now().strftime("%Y-%m-%d"),
    }

class res_partner_request(osv.osv):
    """ Partner analysis elements
    """
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    _columns = {
        'analysis_request_ids':fields.one2many('analysis.supplier.request', 'partner_id', 'Analysis request', required=False),    
    }
res_partner_request()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
