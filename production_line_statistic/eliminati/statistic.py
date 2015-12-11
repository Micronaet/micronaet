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

class mrp_production_workcenter_line_extra(osv.osv):
    ''' Extra elements
    '''
    _name="mrp.production.workcenter.line"
    _inherit="mrp.production.workcenter.line"
    
    # On change method:  #######################################################
    def on_change_line(self, cr, uid, ids, workcenter_id, product, context=None):
        ''' Set up default production elements according to product-workcenter
        '''
        res={}

        if (not workcenter_id) or (not product):
            return {}
        
        default_pool=self.pool.get("mrp.production.workcenter.line.statistic")
        default_ids=default_pool.search(cr, uid, [('product_id','=',product),('workcenter_id','=',workcenter_id)], context=context)
        if not default_ids:
            return res
        
        default_proxy=default_pool.browse(cr, uid, default_ids, context=context)[0]
        res['value']={}
        res['value']['single_cycle_duration']=default_proxy.single_cycle_duration
        res['value']['single_cycle_qty']=default_proxy.single_cycle_qty
        return res
        
    # Button method: ###########################################################
    def save_default_cycle_parameter(self, cr, uid, ids, context=None):
        ''' Button for save cycle parameter as defaulf product-line elements
        '''
        lavoration_proxy=self.browse(cr, uid, ids, context=context)[0]
        statistic_pool=self.pool.get('mrp.production.workcenter.line.statistic')
        
        if not lavoration_proxy.product.id or not lavoration_proxy.workcenter_id.id:
            return False
            
        statistic_ids = statistic_pool.search(cr, uid, [('product_id','=',lavoration_proxy.product.id or False),
                                                        ('workcenter_id','=',lavoration_proxy.workcenter_id.id or False)], context=context)
        
        if statistic_ids:
            modify_res = statistic_pool.write(cr, uid, statistic_ids, {'single_cycle_duration': lavoration_proxy.single_cycle_duration,
                                                                       'single_cycle_qty': lavoration_proxy.single_cycle_qty,
                                                                       }, context=context)            
        else:           
            item_id = statistic_pool.create(cr, uid, {'product_id': lavoration_proxy.product.id,
                                                      'workcenter_id': lavoration_proxy.workcenter_id.id,
                                                      'single_cycle_duration': lavoration_proxy.single_cycle_duration,
                                                      'single_cycle_qty': lavoration_proxy.single_cycle_qty,
                                                      }, context=context)       
        return True
mrp_production_workcenter_line_extra()

class mrp_production_workcenter_line_statistic(osv.osv):
    ''' Statistic for workcenter:
        1. Standard cycle parameter for product-workcenter key
    '''
    _name="mrp.production.workcenter.line.statistic"
    _description="Workcenter statistic"
    _rec_name="product_id"
            
    _columns = { 
               'product_id': fields.many2one('product.product', 'Product', required=True, ondelete='cascade',),
               'workcenter_id': fields.many2one('mrp.workcenter', 'Workcenter Line', required=True, ondelete='cascade',),
               'single_cycle_duration': fields.float('Cycle duration', digits=(8, 3), required=False),        
               'single_cycle_qty': fields.float('Cycle quantity', digits=(8, 3), required=False),             
    }    
mrp_production_workcenter_line_statistic()    

class product_product_statistic(osv.osv):
    ''' Add extra fields for product object
    '''
    _inherit="product.product"
    _name="product.product"
    
    _columns= {
        'workcenter_line_ids': fields.one2many('mrp.production.workcenter.line.statistic', 'product_id', 'Workcenter cycle stats'),        
    }
product_product_statistic()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
