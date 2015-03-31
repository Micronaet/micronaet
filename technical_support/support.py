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

class support_partner_ref(osv.osv):
    ''' Issue element for partner 
        Every partner has a user for log in        
    '''
    
    _name = 'support.partner.ref'
    _description = 'Support partner ref'

    _columns = {
        'name':fields.char('Issue user', size=80, required=False, readonly=False),
        'active':fields.boolean('Active', required=False),
        'opt_in':fields.boolean('Opt. in', required=False, help="If checked every comunication is sent to the email address"),
        'email':fields.char('E-mail', size=80, required=False, readonly=False),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'note': fields.text('Note'),
        # TODO manager or roles?
    }
    
    _defaults = {
        'active': lambda *a: True,
        'opt_in': lambda *a: True,
    }
support_partner_ref()

class res_users_extra_fields(osv.osv):
    ''' Every user has a partner for issue inseriment
    '''
    
    _inherit = 'res.users'
    _name = 'res.users'

    _columns = {
        'external_issue':fields.boolean('External issue', required=False, help="User that remote log in only for insert issue in DB"),
        'partner_issue_id':fields.many2one('res.partner', 'Partner for issue', required=False, help="When insert an issue this partner is use for opening"),
    }
res_users_extra_fields()

class res_partner_extra_fields(osv.osv):
    ''' Extra element for res.partner (like user for partner)
    '''
    
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
        'ref_ids':fields.one2many('support.partner.ref', 'partner_id', 'Issue users', required=False, help="Issue user linked to the partner"),
        'user_issue_ids':fields.one2many('res.users', 'partner_issue_id', 'User', required=False),
    }
res_partner_extra_fields()

class support_area(osv.osv):
    ''' Area that tech are divided into, ex:
        Hardware area, Account area, Software area
    '''
    
    _name = 'support.area'
    _description = 'Support area'
    _columns = {
        'name':fields.char('Area', size=64, required=False, readonly=False),
        'note': fields.text('Note'),
    }
support_area()

class support_area_sector(osv.osv):
    ''' Sector into area are divided, ex:
        Software area divided into sector:
                 OpenERP
                 Web site
                 Scripting
    '''
    
    _name = 'support.area.sector'
    _description = 'Support area sector'
    _columns = {
        'name':fields.char('Sector', size=64, required=False, readonly=False),
        'area_id':fields.many2one('support.area', 'Area', required=False),        
        'note': fields.text('Note'),
    }
support_area_sector()

class support_issue(osv.osv):
    ''' Center element of the module, this is the start point of the problem / 
        issue record, here is the manage of the issue and the comunication 
        generated or Intervent create.
        This object has a linked WF for get the state administration of the 
        record
    '''
    
    _name = 'support.issue'
    _description = 'Support Issue'
    _order = 'name'
    
    # WF state functions:
    def support_draft(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'draft',
                                  #'datetime': time.strftime('%Y-%m-%d %H:%M:%S') # already setted as default
                                  'datetime_received': False,    # Reset date
                                  'datetime_charge': False,    # Reset date
                                  'datetime_working': False,    # Reset date
                                  'datetime_close': False,    # Reset date
                                  'tech_id': False,              # Reset tech
                                  }) 
        return True

    def support_received(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'received', 
                                  'datetime_received': time.strftime('%Y-%m-%d %H:%M:%S'),
                                 }) 
        return True

    def support_charge(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'charge', 
                                  'datetime_charge': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  'tech_id': uid,  # set the user as tech
                                  }) 
        return True

    def support_working(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'working', 
                                  'datetime_working': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  }) 
        return True

    def support_close(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'close', 
                                  'datetime_close': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  }) 
        return True

    def support_cancel(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'cancel', 
                                  'datetime_close': time.strftime('%Y-%m-%d %H:%M:%S'), # same as closing time
                                  }) 
        return True        

    # Defaulf function:
    def _get_partner_linked_to_user(self, cr, uid, context = None):
        ''' Read if user is externat and return partner id
        '''
        user_browse=self.pool.get('res.users').browse(cr, uid, uid)
        if user_browse.external_issue:
           return user_browse.partner_issue_id.id
        return False
       
    def _get_external_linked_to_user(self, cr, uid, context = None):
        ''' Read if user is external 
        '''
        user_browse=self.pool.get('res.users').browse(cr, uid, uid)
        return user_browse.external_issue

    def _get_external_start(self, cr, uid, context = None):
        ''' Start from list
        '''
        user_browse=self.pool.get('res.users').browse(cr, uid, uid)
        if user_browse.external_issue: # only for external users
           return 'openerp'
        return 'phone'  # usually is phone our first contact 

    def _get_external_create_from(self, cr, uid, context = None):
        ''' Create from "customer" if is external user
        '''
        
        user_browse=self.pool.get('res.users').browse(cr, uid, uid)
        if user_browse.external_issue: # only for external users
           return 'customer'
        return 'tech' # Usually is tech that insert problems / issues
 
    # On_change function
    """def on_change_area(self, cr, uid, ids, area_id, context=None):
        ''' Filter sector (and reset value)
        '''    
        import pdb; pdb.set_trace()
        res={'value':{'sector_id':False}, domain:[]}    
        if area_id:       
           res['domain']=[('area_id','=',area_id)]
        return res'''

    '''def on_change_sector(self, cr, uid, ids, sector_id, context=None):
        ''' If change sector (before changing area) this set up correct value
            for area
        '''
        import pdb; pdb.set_trace()
        if sector_id:       
           sector_id = self.pool.get('support.area.sector').browse(cr, uid, sector_id)
           return {
                   'value' : { 'area_id' : sector_id.area_id and sector_id.area_id.id,
                             },
                  },                  
        return {}"""
        

    _columns = {
        # Anagrafic data for issue
        'name':fields.char('subject', size=80, required=True, readonly=False),
        'description': fields.text('Description', help="Description of the issue"),
        'create_from':fields.selection([
            ('tech','Internal tech'),             # Directly the tech
            ('company','Company'),                # People in Company
            ('customer','Customer'),              # The customer (via web or logged in)
            ],'Create from', select=True, readonly=False, help="Create from: tech that manage issue, Company people that assign to tech, Customer that choose only Area"),
        'started_with':fields.selection([
            ('phone','Phone'),                # Phone call
            ('chat','Chat'),                  # chat program
            ('mail','Mail'),                  # e-mail 
            ('web','Web'),                    # web interface
            ('voice','Voice'),                #[ a voice
            ('openerp','OpenERP'),            # directly user log in
            ],'Started with', select=True, readonly=False, help="Issue arrived from this type of sources"),
        'priority':fields.selection([
            ('low','Low'),
            ('medium','Medium'),            
            ('high','High'),            
            ('very_high','Very High'),            
            ],'Priority', select=True, readonly=False),
        'locked':fields.boolean('Locked problem', required=False, help="If checked indicate that the problems is very urgent and lock the use of PC or a particular work"),
        'notify_creator': fields.boolean('Notify user', required="False", help="Notify comunication or other mail to the user that create issue"),
        'note': fields.text('Note'),
        'count': fields.integer('Count'), # Always 1, for graph view (count the issue)

        # People for this issue
        'partner_id':fields.many2one('res.partner', 'Label', required=False), # TODO res.partner address (for contect fetchmail)?
        'user_id':fields.many2one('res.users', 'User', required=False, help="User that insert issue"),
        'tech_id':fields.many2one('res.users', 'Tech user', required=False, help="User that manage or take in charge the issue"),
        'partner_ref_id':fields.many2one('support.partner.ref', 'Customer ref.', required=False, help="Customer internal reference (for sen comunication or information about this issue)"),        
        #'external_issue': fields.related('user_id', 'external_issue', type='char', string='External user'),
        'external_issue': fields.boolean('Esternal issue', required=False),
        # Related fields for reference:
        #'email_user_id': fields.related('user_id','user_email', type='char', string='User email'),
        #'email_partner_id': fields.related('partner_id','email', type='char', string='Partner email'),
        
        # Identificazion of the issue
        'area_id':fields.many2one('support.area', 'Area', required=True, help="Help to pipe the request to the selected area"),        
        'sector_id':fields.many2one('support.area.sector', 'Sector', required=False, help="Help to identificate particular sector of the area"),        

        # time recording:
        'datetime': fields.datetime('Creation date', help="Data of creation issue"),
        'datetime_received': fields.datetime('Received date', help="Data of confirm receiving issue"),
        'datetime_charge': fields.datetime('Charge date', help="Data of get in charge issue"),
        'datetime_working': fields.datetime('Working date', help="Data of start working issue"),
        'datetime_close': fields.datetime('Close date', help="Data of close / cancel issue"),
         
        # Case Study:        
        'is_case':fields.boolean('Is a case study?', required=False),        
        'case_subject':fields.char('Case subject', size=80, required=False, readonly=False, help="Short description of the Issue, something like a title"),
        'case_problem': fields.text('Problem', help="Long description of the problem"),
        'case_solution': fields.text('Solution'),

        # workflow
        'state':fields.selection([
            ('draft','Draft'),       # Issue created
            ('received','Received'), # Send notification that the issue is received
            ('charge','In charge'),  # Set issue in charge to user that trigger the state
            ('working','Working'),   # Start working on it
            ('cancel','Cancel'),     # Set cancel (error inserting)
            ('close','Close'),       # Issue correctly closed
        ],'State', select=True, readonly=True),
    }
    
    _defaults = {
        'locked': lambda *a: False,
        'datetime': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'), # only create has a default
        'user_id': lambda self,cr,uid,context: uid,                # logged user 
        'notify_creator': lambda *a: True,                         # Email to creator user (usually are the customer)
        'priority': lambda *a: 'medium',
        'state': lambda *a: 'draft',
        'count': lambda *a: 1,
        'partner_id': _get_partner_linked_to_user,        # search for externa user the partner_id assigned
        'external_issue': _get_external_linked_to_user,   # search if the user is external
        'started_with': _get_external_start,              # if external user = openerp 
        'create_from': _get_external_create_from,         # create directly from "custome" if external user
        #'partner_id'   # TODO set a default partner_id or res_partner_id to res.users object?
    }
support_issue()

class support_issue_comunication(osv.osv):
    _name = 'support.issue.comunication'
    _description = 'Support issue comunication'
    
    _columns = {
        'name':fields.char('Subject', size=64, required=False, readonly=False),        
        'direction':fields.selection([
            ('tech','To Tech'),               # To customer
            ('customer','To Customer'),       # To customer
            ('supplier','To Supplier'),       # To supplier (for get some informations)
            ('internal','Internal'),          # Internal comunications
            ('info','Information'),           # Information or extra note (usefull for post analysis)
        ],'Direction', select=True, readonly=False, help="Direction of the comunication: to tech that manage issue, to customer, to supplier (for get info), internal (for consulting), info (for extra note that is not a comunication)"),
        'invisible':fields.boolean('Invisible', required=False, help="No reporting about this comunication on print or mail to final user (ex. ask to you supplier something or internat comunications)"),
        'tech_id':fields.many2one('res.users', 'Tech user', required=False, help="Usually is the tech that manage the issue but for some comunication can change this ref."),
        'datetime': fields.datetime('Date', help="Create date of comunication"),        
        'body': fields.text('Comunication body', help="Body text of the message (also used for notificazion or fetched mail"),
        'note': fields.text('Internal note', help="Text usefull for "),
        'issue_id':fields.many2one('support.issue', 'Issue', required=False),
        # TODO variation for res.partner.address
        # destination email not calculated because related: 
        #   issue_id.user_id.user_email   
        #   issue_id.partner_id.email    
    }
    
    _defaults = {
        'datetime': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'), # only create has a default
    }
support_issue_comunication()

class intervention_report_extra_fields(osv.osv):
    """ Create link to intervention.report for manage issue in the intervent       
    """
    _name = 'intervention.report'
    _inherit = 'intervention.report'
    
    _columns = {
        'issue_ids':fields.many2many('support.issue', 'intervent_issue_rel', 'intervent_id', 'issue_id', 'Issue'),
    }
intervention_report_extra_fields()

class support_issue(osv.osv):
    ''' Inherit for add extra _ids fields
    '''
    
    _name = 'support.issue'
    _inherit = 'support.issue'
    
    _columns = {
        'comunication_ids':fields.one2many('support.issue.comunication', 'issue_id', 'Comunications', required=False, help="List of comunication for this issue"),
        'intervent_ids':fields.many2many('intervention.report', 'intervent_issue_rel', 'issue_id', 'intervent_id', 'Intervent'),        
    }
support_issue()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
