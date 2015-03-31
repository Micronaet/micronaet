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

class sale_order_followup_inherit(osv.osv):
    _name = 'sale.order'
    _inherit = 'sale.order'

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
 
        This procedure try to search #customer# if present this particular
        has tag in subject (instead of all followup are setted up for company 
        partner
        Read user that launch email
        Add extra information in notebook page
        Add dashboard visibility 
        
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks
        """
        def _get_user_from_email(self, cr, uid, email, context=None):
           """This function returns partner Id based on email passed
           @param self: The object pointer
           @param cr: the current row, from the database cursor,
           @param uid: the current user’s ID for security checks
           @param from_email: email address based on that function will search for the correct
           """
           from_email = self.pool.get('email.server.tools').to_email(email)[0]
           user_proxy=self.pool.get('res.users')
           user_ids=user_proxy.search(cr,uid,[('user_email','like',from_email)])
           if user_ids:
              return user_ids[0] # only the first element 
           return 1 # else return administrator

        def _get_user_from_subject(self, cr, uid, subject, context=None):
           ''' This function parse user login name from subject, ex.:
               "Quotation for @userxyz@ customer #customer1#
           '''
           at_subject=subject.split("@")
           if len(at_subject)==3:
              user=at_subject[1]
           user_proxy=self.pool.get('res.users')
           user_ids=user_proxy.search(cr,uid,[('login','ilike',user)])
           if user_ids:
              return user_ids[0]

        def _get_customer_from_subject(self, cr, uid, subject, context=None):
           ''' This function parse customer name from subject, ex.:
               "Quotation for @userxyz@ customer #customer1#
           '''
           at_subject=subject.split("#")
           if len(at_subject)==3:
              name=at_subject[1]
              partner_proxy=self.pool.get('res.partner')
              partner_ids=partner_proxy.search(cr,uid,[('name','ilike',name)])
              if partner_ids:
                 return partner_ids[0]
           return False      

        def _get_customer_address(self, cr, uid, partner_id, context=None):
           ''' Get first address # TODO create correct value for order
           '''
           partner=self.pool.get('res.partner').browse(cr,uid,partner_id)
           if partner.address:
              return partner.address[0].id
           else:
              return False   
           
        if context is None: 
            context = {}

        # pool used:
        mailgate_pool = self.pool.get('email.server.tools')
        res_partner_pool = self.pool.get('res.partner')
        res_partner_address_pool = self.pool.get('res.partner.address')

        # default value #TODO search default company!!!!
        partner_id=1 
        partner_address_id=1 
        pricelist_id=1 

        # element used:
        subject = msg.get('subject') or _('No subject')
        body = msg.get('body')
        msg_from = msg.get('from') or msg.get_unixfrom()
        priority = msg.get('priority')
        
        # user:     
        follow_user_id=_get_user_from_email(self, cr, uid, msg_from, context=context)
        user_id=follow_user_id # default if not present

        # partner:
        partner_parsed = False
        parse_partner_id = _get_customer_from_subject(self, cr, uid, subject, context=context)
        if parse_partner_id:
           parse_address_id=_get_customer_address(self, cr, uid, parse_partner_id, context=context)
           if parse_partner_id:
              partner_parsed=True
              res={}
              res['partner_id']=parse_partner_id
              res['partner_address_id']=parse_address_id
              partner=res_partner_pool.browse(cr,uid,res['partner_id'])
              if partner.user_id: # set default agent per client
                 user_id=partner.user_id.id 
              pricelist_id=partner.property_product_pricelist.id

        if not partner_parsed:      
           res = mailgate_pool.get_partner(cr, uid, msg_from)

           if not (res['partner_address_id'] and res['partner_id']): 
              res['partner_id']=partner_id
              res['partner_address_id']=partner_address_id 
           elif res['partner_id']:
              partner=res_partner_pool.browse(cr,uid,res['partner_id'])
              if partner.property_product_pricelist: # set default pricelist per client
                 pricelist_id=partner.property_product_pricelist.id

        # search user for link offer 
        vals = {
            'follow_email_creation': True,
            'follow_subject': subject,
            'follow_email_from': msg_from,
            'follow_email_cc': msg.get('cc'),
            'follow_description': body,
            'follow_user_id': follow_user_id, # send the email
            'user_id': user_id,
            # if occour this is the email list:
            #'follow_message_ids': fields.one2many('mailgate.message', 'res_id', 'Messages', domain=[('model','=',_name)]),
            
            
            # required field for create sale.order
            'pricelist_id': pricelist_id,
            'partner_order_id': res['partner_address_id'],
            'partner_invoice_id': res['partner_address_id'],
            'partner_shipping_id': res['partner_address_id'],
            'partner_id': res['partner_id'],
        }
        # TODO active CRM to get priority list
        #if msg.get('priority', False):
        #    vals['follow_priority'] = priority

        # TODO search also in contact or address
        if res:
            vals.update(res)
            
        res_id = self.create(cr, uid, vals, context=context)
        attachents = msg.get('attachments', [])
        att_ids = []
        for attactment in attachents or []:
            # TODO filter attachment to delete logo and extra info not required
            data_attach = {
                'name': attactment,
                'datas': binascii.b2a_base64(str(attachents.get(attactment))),
                'datas_fname': attactment,
                'description': 'Mail attachment',
                'res_model': self._name,
                'res_id': res_id, 
            }
            att_ids.append(self.pool.get('ir.attachment').create(cr, uid, data_attach))
        return res_id, att_ids

    def message_update(self, cr, uid, ids, vals=None, msg="", default_act='pending', context=None):
        """
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of update mail’s IDs
        """
        return True

    def msg_send(self, cr, uid, id, *args, **argv):

        """ Send The Message
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of email’s IDs
            @param *args: Return Tuple Value
            @param **args: Return Dictionary of Keyword Value
        """
        return True
    
    _columns = {
        'follow_email_creation':fields.boolean('Create by mail', required=False),
        'follow_subject': fields.char('Subject', size=128, required=False, readonly=False),
        'follow_date': fields.datetime('Date'),
        'follow_email_from': fields.char('From', size=128, required=False, readonly=False),
        'follow_email_cc': fields.char('CC', size=128, required=False, readonly=False),
        'follow_description': fields.text('Body'),
        'follow_user_id': fields.many2one('res.users', 'User', required=False), # TODO c'è già in sale.order?
        #'follow_priority': fields.selection(crm.AVAILABLE_PRIORITIES, 'Priority'),
        'follow_message_ids': fields.one2many('mailgate.message', 'res_id', 'Messages', domain=[('model','=',_name)]), # TODO serve (qui solo una)?
        'count': fields.integer('Count'), # for count in graph
        
        #'partner_id': fields.many2one('res.partner', 'Partner', required=False),
        #'address_id': fields.many2one('res.partner.address', 'Partner', required=False),
        #'order_id':fields.many2one('sale.order', 'Order', required=False),
    }
    _defaults = {
                'follow_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
                'follow_email_creation': lambda *a: False,
                'count': lambda *a: 1,
                }
sale_order_followup_inherit()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
