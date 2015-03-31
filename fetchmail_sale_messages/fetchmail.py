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
from datetime import datetime
from tools.translate import _
import time
import binascii
import tools

class sale_order_comunication(osv.osv):
    _name = 'sale.order.comunication'
    _description = 'Sale Comunication'

    _order = 'date'

    def message_followers(self, cr, uid, ids, context=None):
        """ Get a list of emails of the people following this thread
        """
        res = {}.fromkeys(ids, ())
        #for case in self.browse(cr, uid, ids, context=context):
        #    l=[]
        #    if case.email_cc:
        #        l.append(case.email_cc)
        #    if case.user_id and case.user_id.user_email:
        #        l.append(case.user_id.user_email)
        #    res[case.id] = l
        return res

    def message_new(self, cr, uid, msg, context=None):
        """
        Automatically calls when new email message arrives
        Called from fetchmail module

        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks
        """
        mailgate_pool = self.pool.get('email.server.tools')

        subject = msg.get('subject') or _("No Subject")
        #import pdb; pdb.set_trace()
        
        parse_subject=subject.split("##")
        if len(parse_subject)==3:
           if parse_subject[1][:2]=="ID":  # format Subject ##ID:123##
              order_id = long(parse_subject[1][3:] or 0) 
           else:                       # format Subject ##SO016##
              #import pdb; pdb.set_trace()
              order_ids = self.pool.get('sale.order').search(cr, uid, [('name','=',parse_subject[1])])
              if order_ids:
                 order_id = order_ids[0]
              else:
                 order_id=0 # TODO comunicare errore e non scrivere il record  
        else:
           order_id=0 # TODO comunicare errore e non scrivere il record
  
        body = msg.get('body')
        if body:
           parse_body=body.split("##")        
        else:
           parse_body=['']   
        msg_from = msg.get('from')
        priority = msg.get('priority')

        vals = {
            'name': parse_subject[0], # first part
            'email_from': msg_from,
            'email_cc': msg.get('cc'),
            'description': parse_body[0],
            'user_id': 1, # TODO administrator
            'order_id': order_id,
        }
        #if msg.get('priority', False):
        #    vals['priority'] = priority

        res = mailgate_pool.get_partner(cr, uid, msg.get('from') or msg.get_unixfrom())
        if res:
            vals.update(res)

        res = self.create(cr, uid, vals, context)
        #attachents = msg.get('attachments', [])
        att_ids = []
        #for attactment in attachents or []:
        #    data_attach = {
        #        'name': attactment,
        #        'datas':binascii.b2a_base64(str(attachents.get(attactment))),
        #        'datas_fname': attactment,
        #        'description': 'Mail attachment',
        #        'res_model': self._name,
        #        'res_id': res,
        #    }
        #    att_ids.append(self.pool.get('ir.attachment').create(cr, uid, data_attach))

        return res, att_ids
    
    _columns = {
        'name': fields.char('Subject', size=64, required=False, readonly=False),
        'date': fields.datetime('Date'),
        'email_from': fields.char('From', size=64, required=False, readonly=False),
        'email_cc': fields.char('CC', size=64, required=False, readonly=False),
        'description': fields.text('Body'),
        'user_id': fields.many2one('res.users', 'User', required=False),
        'partner_id': fields.many2one('res.partner', 'Partner', required=False),
        'address_id': fields.many2one('res.partner.address', 'Partner', required=False),
        'order_id':fields.many2one('sale.order', 'Order', required=False),
    }
    _defaults = {
                'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
                }
sale_order_comunication()

class sale_order_extra_fields(osv.osv):
    _name='sale.order'
    _inherit ='sale.order'

    _columns = {
               'comunication_ids':fields.one2many('sale.order.comunication', 'order_id', 'Comunications', required=False),
               }
sale_order_extra_fields()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
