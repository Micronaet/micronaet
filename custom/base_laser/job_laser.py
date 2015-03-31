# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://axelor.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv, fields

class res_partner_job_add_fields(osv.osv):
    _name = 'res.partner.job'
    _inherit = 'res.partner.job'

    def _get_function_value(self, cr, uid, val, context=None):
        ''' Change with search the value of function of job in the one 
            finded in the list
            if not find return capitalize function'''
        if val:
           function_ids=self.pool.get('training.config.contact.function').search(cr,uid,[('kind', 'ilike', 'standard'),('function', 'ilike', val)], context=context)
           function_read=self.pool.get('training.config.contact.function').read(cr, uid, function_ids, context=context)
           if function_read:
              return function_read[0]['function']
        return val.capitalize()

    def create(self, cr, uid, vals, context=None):
        '''Override del metodo create per sovrascrivere la funzione''' 
        if 'function' in vals:
           vals['function']=self._get_function_value(cr, uid, vals['function'], context=context) 
        return super(res_partner_job_add_fields, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        '''Override del metodo write per sovrascrivere la funzione''' 
        if 'function' in vals:
           vals['function']=self._get_function_value(cr, uid, vals['function'], context=context) 
        return super(res_partner_job_add_fields, self).write(cr, uid, ids, vals, context=context)

    _columns = {
        'prev_id': fields.integer('Import linked ID'),
        #'subscription_line_ids' : fields.one2many('training.subscription.line', 'job_id',
        #                                          'Iscrizioni del contatto'),
        }
res_partner_job_add_fields()
