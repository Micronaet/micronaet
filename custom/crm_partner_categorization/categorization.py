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

'''
class crm_contact_state(osv.osv):
    _name = 'crm.contact.state'
   
    _columns = {
                'name':fields.char('Name', size=64, required=True, readonly=False),
                'colour': fields.selection(color_list,
                    help='Colour that represent activity on partner, \
                                 Green=Earlyed contacted \
                                 Yellow=Contact in the year \
                                 Red=Cold contact, over a year \
                                 Black=Not yet contacted',                                 
                    string='State of contact', select=True, readonly=False), 
                'generic_contact':fields.boolean('Generic contact', required=False,
                    help='Allow to specify the day of contact for all CRM object'),
                # generic contact or this particular contact (depends on check): 
                'contact_period': fields.integer('Contact period', 
                    help='Period (in day: <=number of day) that there is a generic contact',),
                'contact_period_lead': fields.integer('Contact period lead', 
                    help='Period (in day: <=number of day) that a lead must be to belong to this category',),
                'contact_period_opportunity': fields.integer('Contact period opportunity', 
                    help='Period (in day: <=number of day) that an opportunity must be to belong to this category',),
                'contact_period_phone': fields.integer('Contact period phone',
                    help='Period (in day: <=number of day) that a phone call must be to belong to this category',),
                'contact_period_email': fields.integer('Contact period email',
                    help='Period (in day: <=number of day) that an email must be to belong to this category',),
                'note': fields.text('Note', help='Some information to this control state behaviours'),       
                }
                
    _defaults = {
                'generic_contact': lambda *x: True,
                } 
                                               
    _order = 'name'               
crm_contact_state()
'''

'''
class crm_partner_category(osv.osv):
    _name = 'crm.partner.category'
    
    _columns = {
                'name': fields.char('Name', size=64, required=True, readonly=False),
                'check_activity': fields.boolean('Check CRM activity', required=False,
                    help='For represent categorization color check CRM activity \
                          if not color is the selected one here'),
                'colour': fields.selection(color_list,
                    help='Normal representation of this partner, \
                                 Green=contact \
                                 Yellow=try a contact (not hot) \
                                 Red=cold customer, do not contact \
                                 Black=Not yet decided',                                 
                    string='Normal representation', select=True, readonly=False),
                'note': fields.text('Note', help='Some information to this category behaviours'),                
               }
crm_partner_category()   
'''

class crm_partner_importance(osv.osv):
    _name = 'crm.partner.importance'
    
    _columns = {
                'name': fields.char('Name', size=10, required=True, 
                        readonly=False, help='ex.: **** or xxxx'),
                'symbol_description': fields.char('Symbol description', size=64, required=False, readonly=False),
                'sequence': fields.integer('Sequence', help='Order of importance level'),
                'note': fields.text('Note', help='Some information to this level behaviours'),       
                'invoiced_less_than': fields.float('Invoice less than', digits=(16, 2)),                         
                'invoiced_over_than': fields.float('Invoice over than', digits=(16, 2)),                         
               }
    
    _order = 'sequence'           
crm_partner_importance()   

class res_partner_categorization_fields(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def _get_last_activity(self, cr, uid, ids, args, field_list, context=None):
        '''
        Get last activity date:
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param context: A standard dictionary for contextual values
        @return: list of dictionary which contain partner id, colour
        '''
        if context is None: 
           context={}
        
        res = dict.fromkeys(ids, 'no contacts')
        '''#import pdb; pdb.set_trace()
        #if ids:
           # get order
           #cr.execute("select id, max(date_order) from sale_order where id in (" + ",".join(["%s"] * len(ids)) + ")", ids)
           #elements=cr.fetchall()
           #for item_id, element in elements:
           #    res[item_id]= "ORD %s" % (element,)
           last_date = result and result[0] or False
           if last_date:
               period_start = datetime.strptime(last_date,"%Y-%m-%d %H:%M:%S")+ relativedelta(days=1)
               period_start = period_start - relativedelta(hours=period_start.hour, minutes=period_start.minute, seconds=period_start.second)
           else:
               period_start = datetime.today()
           return period_start.strftime('%Y-%m-%d')'''
           

        return res

    _columns = {
               'partner_color': fields.selection([
                   ('green','Green'),
                   ('yellow','Yellow'),
                   ('red','Red'),
                   ],'Color classification', select=True, readonly=False),
               'partner_importance_id':fields.many2one('crm.partner.importance', 'Importance', required=False),               
               'last_activity': fields.function(_get_last_activity, method=True, type='char', size=30, string='Last activity', store=True,),
               } 
res_partner_categorization_fields()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
