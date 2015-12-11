#!/usr/bin/python
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
import time
import pdb

class chemical_analysis_partner(osv.osv):
    ''' Form that keep trace of specific request for partner-product
    '''

    _name = 'chemical.analysis.partner'
    _description = 'Chemical analysis partner'

    def button_load_from_model(self, cr, uid, ids, context = None):
        #pdb.set_trace()
        chemical_proxy = self.browse(cr, uid, ids, context = context)[0]
        actual = [item.name.id for item in chemical_proxy.analysis_line_ids]
        if chemical_proxy.name.model_id:
            for item in chemical_proxy.name.model_id.analysis_line_ids:
                if item.name.id not in actual:
                    self.pool.get('chemical.analysis.partner.line').create(cr, uid, {
                        'name': item.name.id,
                        'from': item.min,
                        'to': item.max,
                        'analysis_id': chemical_proxy.id,
                    }, context = context)
        return True

    def button_analysis_new_version(self, cr, uid, ids, context = None):
            ''' Copy current versione and create a new with version incremented
                (disable current so no partner showing)
            '''
            analysis_proxy = self.browse(cr, uid, ids, context = context)[0]
            self.write(cr, uid, ids, {'is_active':False}, context = context)
            analysis_id = self.create(cr, uid, {
                        'version':analysis_proxy.id + 1,
                        'name': analysis_proxy.name.id,
                        'partner_id': analysis_proxy.partner_id.id,
                        'is_active':True,
                        'date': analysis_proxy.date,
                        }, )
            for line in analysis_proxy.analysis_line_ids:
                self.pool.get('chemical.analysis.partner.line').create(cr, uid, {
                        'name': line.name.id,
                        'from': line.__getattr__('from'),
                        'to': line.to,
                        'analysis_id': analysis_id,
                        }, context = context)
            return True

    def onchange_version(self, cr, uid, ids, partner_id, product_id, context = None):
        ''' Change analysis version
        '''
        #pdb.set_trace()
        res={'value':{}}
        if product_id and partner_id:
            cr.execute("select max(version) from chemical_analysis_partner where is_active=TRUE AND partner_id = %s AND name = %s" %(partner_id, product_id))
            try:
                max = cr.fetchone()[0]
                res['value']['version'] = max + 1
            except:
                res['value']['version'] =  1
        else:
            res['value']['version'] = False
        return res

    _columns = {
            'name':fields.many2one('product.product', 'Product', required=True),
            #'model':fields.related('product_id', 'model_id', type='many2one', relation='chemical_analysis', string='Model', store=True, required=True),
            'is_active': fields.boolean('Active'),
            'partner_id': fields.many2one('res.partner', 'Partner'),
            'version': fields.integer('Version'),
            'date': fields.date('Date'),
    }

    _defaults = {
        'is_active': lambda *a: True,
        'version': lambda *a: 1,
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }

class chemical_analysis_partner_line(osv.osv):
    ''' Lines of partner-product form
    '''
    
    _name = 'chemical.analysis.partner.line'
    _description = 'Chemical analysis partner line'

    _columns = {
         'name':fields.many2one('chemical.element', 'Elements', required = True),
         'from':fields.float('From', required = False),
         'to':fields.float('To', required = False),
         'analysis_id': fields.many2one('chemical.analysis.partner', 'Partner analysis'),
    }

class chemical_analysis_partner(osv.osv):
    ''' Inherit for *2many fields
    '''
    _name = 'chemical.analysis.partner'
    _inherit = 'chemical.analysis.partner'

    _columns = {
        'analysis_line_ids':fields.one2many('chemical.analysis.partner.line', 'analysis_id', 'Details'),
    }

class res_partner(osv.osv):
    ''' Add extra analysis to partner
    '''
    
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
        'chemical_ids': fields.one2many('chemical.analysis.partner', 'partner_id', 'Partner'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
