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
import time

class chemical_application_category(osv.osv):
    ''' First group that can define a particular application
    '''
    _name="chemical.application.category"
    _description="Category chemical application"
    _order="seq,name"
    
    _columns = {
               'name': fields.char('name', size=64, required=True, readonly=False, translate=True),
               'seq': fields.integer('seq', required=False, readonly=False),               
               }
chemical_application_category()

class chemical_application(osv.osv):
    _name = 'chemical.application'
    _description = 'Chemical Application'
    _rec_name = 'product_id'
    _order = 'partner_id,product_id'
    
    def _function_number_of_application(self, cr, uid, ids, field_name, arg, context = None):
        """ Test if there's some line in cemical.application
            if so return True else False
        """    
        res = {}
        for item in self.browse(cr, uid, ids):
            res[item.id]=len(item.line_ids)
        return res
        
    _columns = {
        'product_id':fields.many2one('product.product', 'Product', required=True),
        'partner_id':fields.many2one('res.partner', 'Partner', required=True),        
        
        'number_of_application': fields.function(_function_number_of_application, method=True, type='integer', string='# of apps', store=True),

        'mexal_age_description': fields.related('partner_id','mexal_age_description', type='char', size=60, string='Agent'),
        'user_id': fields.related('partner_id','user_id', type='many2one', relation='res.users', string='Responsible', store=True),
        'supervisor_id': fields.related('partner_id','supervisor_id', type='many2one', relation='res.users', string='Supervisor', store=True),        
    }    
chemical_application()

class chemical_application_line(osv.osv):
    _name = 'chemical.application.line'
    _description = 'Chemical application line'
    _order = "date,name"

    _columns = {
        'name':fields.text('Application', required=True, readonly=False),

        'date': fields.date('From date'),
        'date_end': fields.date('To date'),

        'application_id':fields.many2one('chemical.application', 'Application', required=True, on_delete='cascade'),
        'note':fields.text('Note', required=False, readonly=False, help='Internal information/annotation about this use'),
        'valutation':fields.text('Valutation', required=False, readonly=False, help='General valutation for product usage, positive or negative'),

        'partner_id': fields.related('application_id','partner_id', type='many2one', relation='res.partner', string='Partner'),
        'product_id': fields.related('application_id','product_id', type='many2one', relation='product.product', string='Product'),
        'category_id':fields.many2one('chemical.application.category', 'Category', required=False),
        # TODO inserire le prestazioni (con colorazione delle righe)
    }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }
chemical_application_line()

class chemical_application(osv.osv):
    _inherit = 'chemical.application'
    _name = 'chemical.application'
    
    _columns = {
        'line_ids':fields.one2many('chemical.application.line', 'application_id', 'Application', required=False),
    }
chemical_application()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
