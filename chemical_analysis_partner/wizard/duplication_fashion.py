#|/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
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
import pdb

class fashion_duplication(osv.osv_memory):
    '''Table that manages the duplication
    '''
    _name = 'fashion.duplication'
    _description = 'Duplication'

    _columns = {
         'duplication': fields.selection([
                                        ('version', 'New Version'),
                                        ('form', 'New Form'),
                                         ], 'Duplication', select=True),
         'code': fields.char('New code', size=10),
               }

    _defaults = {
         'duplication': lambda *a: 'version',
                }

    def duplication (self, cr, uid, ids, context=None):
        pdb.set_trace()
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        form_pool = self.pool.get('fashion.form')
        product_pool = self.pool.get('product.product')
        form_proxy = form_pool.browse(cr, uid, context.get('active_id', 0), context=context) #TODO comunicare errore nel caso non ci sia active_id
        if wiz_proxy.duplication == 'version':
            model = form_proxy.model
            review = form_proxy.review + 1
        else:
            name = wiz_proxy.code
            review = 0
        original = '%s.%s' %(form_proxy.model,form_proxy.review)
        data = {
               'name': form_proxy.name,
               }
        product_id = product_pool.create(cr, uid, data, context=context)
        data = {
             'model': form_proxy.model,
             'size_base': form_proxy.size_base,
             'size_measure': form_proxy.size_measure,
             'review': form_proxy.review,
             'date': form_proxy.date,
             'original': '%s.%s' %(form_proxy.model,form_proxy.review),
             'h_lining': form_proxy.h_lining,
             'mt_lining': form_proxy.mt_lining,
             'cost_lining': form_proxy.cost_lining,
             'conformed': form_proxy.conformed,
             'start': form_proxy.start,
             'ironing': form_proxy.ironing,
             'area': form_proxy.area,
             'user_id': form_proxy.user_id.id,
             'cut': form_proxy.cut,
             'size': form_proxy.size,
             'colors': form_proxy.colors,
             'article_id': form_proxy.article_id.id,
             'season_id': form_proxy.season_id.id,
             
             'product_id': product_id,
             'state': 'draft',
             }
        form_id = form_pool.create(cr, uid, data, context=context)
        return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'fashion.form', # object linked to the view
            #'views': views,
            'domain': [('id', '=', form_id)], 
            #'views': [(view_id, 'form')],
            #'view_id': False,
            'type': 'ir.actions.act_window',
            #'target': 'new',
            'res_id': form_id,  # IDs selected
            # TODO domain for filter?
           }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
