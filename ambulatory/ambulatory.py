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

class res_partner_extra(osv.osv):
    """
    res_partner_extra
    """
    
    _inherit = 'res.partner'
    _name = 'res.partner'
    _columns = {
        'order_ids':fields.one2many('sale.order', 'partner_id', 'Order', required=False,), # domain="[('state','=','invoice_except')]"),
    }
res_partner_extra()
class demo_room(osv.osv):
    _name = 'demo.room'
    _description = 'Stanza'
    _columns = {
        'name':fields.char('Stanza', size=64, required=False, readonly=False),
        'company_id': fields.many2one('res.company', 'Company', select=True),        
    }
    _defaults = {
        'name': lambda *a: '',
    }
demo_room()
'''class account_analytic_account(osv.osv):
    """ Add extra fields to account.analytic.account
    """
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'
    
    _columns = {
        #'default_to_invoice': fields.many2one('hr_timesheet_invoice.factor', 'Default invoice', help="Defaulf invoice type if there's one active for customer. All intervent are, for default, setted to this value"),
        #'total_hours': fields.float('Total hour', digits=(16, 2), help="Total hour for this contract for all period"),        
    }
account_analytic_account()'''

'''class res_partner_extra_fields(osv.osv):
    """ Add extra field to partner for intervent manage
    """
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    _columns = {
        'trip_duration': fields.float('Trip duration', digits=(16, 2), help="Trip hour duration dealed with the partner"),
        'has_contract': fields.boolean('Has contract', help="Contract for assistence, if yes compile also the analytic account"),
        'default_contract_id': fields.many2one('account.analytic.account', 'Default Contract', help="Defaulf contract if there's one active for customer. All intervent are, for default, setted to this value"),
    }
res_partner_extra_fields()'''

class hr_analytic_timesheet_extra(osv.osv):
    ''' Add extra fields to intervent 
    '''
    _name = 'hr.analytic.timesheet'
    _inherit = 'hr.analytic.timesheet'
    _order = 'date_start'
    
    # Workflow function:
    def intervention_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft',}) 
        return True

    def intervention_waiting(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'waiting',}) 
        return True

    def intervention_confirmed(self, cr, uid, ids, context=None):
        ''' Test if is not present ref, calculate and change status
        '''
        data={'state': 'confirmed',}
        #ref=self.get_sequence_if_not_present(cr, uid, ids, context=context)
        #if ref:
        #    data['ref']=ref
        self.write(cr, uid, ids, data) 
        return True

    def intervention_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel',})
        return True

    def intervention_close(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'close',})
        return True

    def intervention_report_close(self, cr, uid, ids, context=None):
        ''' Test if is not present ref, calculate and change status
        '''
        self.write(cr, uid, ids, {'state': 'reported',})
        return True
    
    # Utiliy function for workflow:
    def get_sequence_if_not_present(self, cr, uid, ids, context=None):
        ''' test if ids element don't have ref setted, if not get next value
        '''
        item_proxy=self.browse(cr, uid, ids[0], context=context)
        if not item_proxy.ref:
           return self.get_intervent_number(cr, uid, context = context)
        return False

    def intervention_report_send_and_close(self, cr, uid, ids, context=None):
        ''' This function opens a window to compose an email, with the intervent template message loaded by default
        '''
        #assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        #ir_model_data = self.pool.get('ir.model.data')
        #try:
        #    template_id = ir_model_data.get_object_reference(cr, uid, 'intervention_report', 'email_template_timesheet_intervent')[1]
        #except ValueError:
        #    template_id = False
        #try:
        #    compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        #except ValueError:
        #    compose_form_id = False
        #ctx = dict(context)
        #ctx.update({
        #    'default_model': 'hr.analytic.timesheet',
        #    'default_res_id': ids[0],
        #    'default_use_template': bool(template_id),
        #    'default_template_id': template_id,
        #    'default_composition_mode': 'comment',
        #    'mark_intervent_as_sent': True
        #})
        #return {
        #    'type': 'ir.actions.act_window',
        #    'view_type': 'form',
        #    'view_mode': 'form',
        #    'res_model': 'mail.compose.message',
        #    'views': [(compose_form_id, 'form')],
        #    'view_id': compose_form_id,
        #    'target': 'new',
        #    'context': ctx,
        #}
        return True
    
    # On change event:
    def on_change_name(self, cr, uid, ids, name, intervention_request, context=None):
        ''' Test if change name, then write it in intervention_request if empty
            No changes if name is empty
        '''
        #if not intervention_request and name:
        #   return {'value': {'intervention_request':name}}
        return {}

    def on_change_mode(self, cr, uid, ids, mode, context=None):
        ''' If change mode:
            test if is customer so trip is required
        '''
        res={}
        
        #res['value']={'trip_require': mode=='customer'} # True if customer
        return res
                
    def on_change_partner(self, cr, uid, ids, partner_id, account_id, context=None):
        ''' If change partner:
            set up account_id if there's default 
            change trip hour if mode setted up to 'customer'        
        '''  
        res={}
        #res['value']= {}
        #if not partner_id:
        #    res['value']['account_id']=False
        #    res['value']['trip_hour'] = 0.0
        #    return res

        #partner_proxy=self.pool.get("res.partner").browse(cr, uid, partner_id, context=context)
        #res['value']['account_id'] = partner_proxy.default_contract_id.id if partner_proxy.default_contract_id else False
        #res['value']['trip_hour'] = partner_proxy.trip_duration # hide if non required
        return res

    def on_change_account(self, cr, uid, ids, account_id, partner_id, user_id=False, context=None):
        ''' Test if change account, then write, if present, to_invoice field
        '''
        #res={'value':{'partner_id':partner_id,}} # default
        #if account_id:
        #   account_proxy=self.pool.get("account.analytic.account").browse(cr, uid, account_id, context=context)
        #   if account_proxy.default_to_invoice: # change only if present (else default pay intervent)
        #       res['value']['to_invoice']=account_proxy.default_to_invoice.id
        #else: # return default value if empty
        #   res['value']['to_invoice']=self.get_default_invoice_value(cr, uid, context=context)
        return {}#res

    def on_change_duration_elements(self, cr, uid, ids, intervent_duration,manual_total,manual_total_internal,trip_require,trip_hour,break_require,break_hour,context=None):
        ''' Calculate total duration and total intenal duration depending on 
            parameter passed
            (TODO: cost)
        '''
        #res={'value':{}}#

        #total = (intervent_duration or 0.0) - \
        #        (break_hour if break_require else 0.0) + \
        #        (trip_hour if trip_require else 0.0)
        
        #if not manual_total:
        #    res['value']['intervent_total'] = total
        #if not manual_total_internal:
        #    res['value']['unit_amount'] = total
        return {} #res        
        
    # Function override for mail:
    def message_post(self, cr, uid, thread_id, **kwargs):
        """ Override related to res.partner. In case of email message, set it as
            private:
            - add the target partner in the message partner_ids
            - set thread_id as None, because this will trigger the 'private'
                aspect of the message (model=False, res_id=False)
        """
        return True
        
    # default function:
    """def get_default_invoice_value (self, cr, uid, context=None):
        ''' Get default invoice depend on xml data imported with module
        '''
        ids=self.pool.get('ir.model.data').search(cr, uid, [('model','=','hr_timesheet_invoice.factor'),('name','=','working_intervent_100')], context=context)
        if ids:
            res_id=self.pool.get('ir.model.data').read(cr, uid, ids, ('id','res_id'), context=context)            
            return res_id[0]['res_id']
        return # nothing (no default)    """
    
    """def get_intervent_number(self, cr, uid, context = None):
        ''' Get intervent sequence number
        '''
        res=self.pool.get('ir.sequence').get(cr, uid, 'hr.intervent.report')        
        return res"""
        
    _columns={
        'ref':fields.char('Rif.', size=12, required=False, readonly=False, help="Progressivo"),
        'intervent_partner_id':fields.many2one('res.partner', 'Cliente', required=False),
        'offer_id':fields.many2one('sale.order', 'Ordine di rif.', required=False),
        'intervention_request': fields.text('Richiesta intervento', help="Tiene traccia della richiesta iniziale"),
        'intervention': fields.text('Intervento', help="Intervento effettuato"),
        'internal_note': fields.text('Note interne', help="Note interne per informazioni che non vengono comunicate al cliente"),        
        'date_start': fields.datetime('Data/ora inizio'), 
        'company_id': fields.many2one('res.company', 'Company', select=True),
        'room_id': fields.many2one('demo.room', 'Stanza', select=True),
        #'date_end': fields.datetime('Date end'),         # TODO evauluate if necessari
        #'intervent_duration': fields.float('Durata', digits=(16, 6), help="Durata intervento"),
        #'intervent_total': fields.float('Duration intervent', digits=(16, 6), help="Duration intervent considering trip and break used for invoice (q. for customer)"),
        #'manual_total':fields.boolean('Manual', required=False, help="If true don't auto calculate total hour, if false, total hours=intervent + trip - pause hours"),
        #'manual_total_internal':fields.boolean('Manual (internal)', required=False, help="If true don't auto calculate total internal hour, if false, total hours=intervent + trip - pause hours"),
        #'trip_require':fields.boolean('Trip', required=False),
        #'trip_hour': fields.float('Trip hour', digits=(16, 6)),
        #'break_require':fields.boolean('Break', required=False, help='If intervention is split in 2 part for break'),
        #'break_hour': fields.float('Break hour', digits=(16, 6), help='Duration of break'),
        # Google maps trip manage:
        #'google_from':fields.selection([
        #    ('previous','Previous'),
        #    ('home','Home'),
        #    ('company','Company'),
        #    ],'From', select=True, readonly=False, help="Used for auto trace route 'from' with google maps"),        
        #'google_to':fields.selection([
        #    ('next','Next'),
        #    ('home','Home'),
        #    ('company','Company'),
        #    ],'To', select=True, readonly=False, help="Used for auto trace route 'to' with google maps"),        
        # Valutare se tenere:
        #'type_id':fields.many2one('intervention.type', 'Type', required=False),  
        # TODO valutare se è il caso di tenere un prodotto per il settore
        #'sector_id':fields.many2one('intervention.sector', 'Sector', required=False, help="List of sector of intervent, used in sector study for division of activity intervents"),

        #'mode':fields.selection([
        #    ('phone','Phone'),
        #    ('customer','Customer address'),
        #    ('connection','Tele assistence'),
        #    ('company','Company address'),],'Mode', select=True, required=True,readonly=False),
        'state':fields.selection([
            ('cancel', 'Annullato'),               # Appointment cancel
            ('draft', 'Bozza'),                    # Intervent / appointment marked on agenda
            ('waiting', 'Attesa conferma'),  # Appointment await confirm from customer
            ('confirmed', 'Confermato'),            # Appointment confirmet
            ('close', 'Eseguito'),                 # Appointment close without sending intervent report
            #('reported', 'Close reported'),     # Appointment close with sending intervent report
        ],'Stato', select=True, readonly=True),    
        
        # Eliminabili
        #'hour_contract': fields.related('partner_id','hour_contract', type='float', digit=(16,2), string='Hour contract'),
    }
    
    _defaults={
         # set working data from xml file as default
         'name': lambda *a: False,
         #'to_invoice': lambda s, c, uid, ctx: s.get_default_invoice_value(c, uid, context=ctx),
         #'ref': lambda s, c, uid, ctx: s.get_intervent_number(c, uid, context=ctx),
         'state': lambda *a: 'draft',
         #'mode': lambda *a: 'connection',
         #'manual_total': lambda *x: False,
         #'user_id': lambda obj, cr, uid, context: uid,
    }
hr_analytic_timesheet_extra()

class sale_order_extra(osv.osv):
    """
    sale_order_extra
    """
    
    _inherit = 'sale.order'
    _columns = {
        'intervent_ids':fields.one2many('hr.analytic.timesheet', 'offer_id', 'Interventi', required=False),
    }
sale_order_extra()

"""class mail_compose_intervent_message(osv.Model):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context=None):
        import openerp.netsvc
        context = context or {}
        if context.get('default_model') == 'hr.analytic.timesheet' and context.get('default_res_id') and context.get('mark_intervent_as_sent'):
            context = dict(context, mail_post_autofollow=True)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'hr.analytic.timesheet', context['default_res_id'], 'intervention_report_close', cr)
        return super(mail_compose_intervent_message, self).send_mail(cr, uid, ids, context=context)"""

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
