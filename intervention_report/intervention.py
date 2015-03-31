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

from osv import osv, fields

class res_partner_extra_fields(osv.osv):
    """ Add extra field to partner for intervent manage
    """
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    _columns = {
        'trip_duration': fields.float('Trip duration', digits=(16, 2)),
        'has_contract': fields.boolean('Has contract',),
        'hour_contract': fields.float('Hour contract', digits=(16, 2), help="If customer has contract this are the hour per year to cover"), # TODO use analytic account?
    }
res_partner_extra_fields()

class intervention_type(osv.osv):
    ''' Type of intervent, like free, contract, warranty etc.
    '''
    _name = 'intervention.type'
    _description = 'Intervention Type'
    _columns = {
        'name' : fields.char('Description', size=64, required=False, readonly=False,),
        'invoice' : fields.boolean('Invoice', required=False, help='If so the intervention will be invoiced for duration time',),
    }
    _defaults = {
        'invoice': lambda *a: True,
    }
intervention_type()

class intervention_sector(osv.osv):
    ''' Sector for the type of intervent, used to link hours to a particular product
        (for ex. passing to account program the intervent)
    '''
    _name = 'intervention.sector'
    _description = 'Intervention sector'
    _columns = {
        'name' : fields.char('Sector', size=64, required=True, readonly=False, help="Sector name, for identify tipology of intervent as it's linked to the product"),
        'product_id':fields.many2one('product.product', 'Product', required=True),
        'note': fields.text('Note'),
    }
intervention_sector()

class intervention_report(osv.osv):
    '''Object to manage calendar plan and report for close intervention 
    '''
    
    _name = 'intervention.report'
    _description = 'Intervention Report'

    # on change event:
    def on_change_name(self, cr, uid, ids, name, intervention_request, context=None):
        ''' Test if change name, then write it in intervention_request if empty
            No changes if name is empty
        '''
        if not intervention_request and name:
           return {'value': {'intervention_request':name}}
        return {}

    def on_change_compute_total_hour(self, cr, uid, ids, duration, trip_require, trip_hour, partner_id, break_require, break_hour, manual_total, context=None):
        ''' Get all value and information for calculate total interventi (also if it has not to calculate)        
        '''
        res={'value': {}}

        # TODO insert searching for trip hour if empty value

        # extra test:
        trip_hour = trip_hour or 0.0 # TODO default value (1.0?)
        if trip_require:
           if not trip_hour and partner_id: # for change
              partner_proxy = self.pool.get('res.partner').browse(cr, uid, partner_id)
              trip_hour = partner_proxy.trip_duration or 0.0
        else:
           trip_hour= 0.0 
        res['value']['trip_hour'] = trip_hour
           
        if break_require:
           if not break_hour:
              break_hour = 0.5
        else:   
           break_hour = 0.0

        res['value']['break_hour'] = break_hour

        if not manual_total: # Calculate total:    
            res['value']['total'] = (duration or 0.0) + (trip_hour or 0.0 if trip_require else 0.0) - (break_hour or 0.0 if break_require else 0.0)
        return res
        
        
    _columns = {# TODO: manage intersection with planning (type of plan: non intersection)
        'name':fields.char('Description', size=64, required=False, readonly=False),
        'ref':fields.char('Ref.', size=12, required=False, readonly=False),
        'import_id': fields.integer('Import ID'),
        'imported':fields.boolean('Imported', required=False),
        'date_start': fields.datetime('Date start'),
        'duration': fields.float('Duration', digit=(5,2)),        
        'date_end': fields.datetime('Date end'),        
        'partner_id':fields.many2one('res.partner', 'Partner', required=True),
        'hour_contract': fields.related('partner_id','hour_contract', type='float', digit=(16,2), string='Hour contract'),
        'total': fields.float('Number of hours', digits=(16, 6)),
        'manual_total':fields.boolean('Manual', required=False, help="If true don't auto calculate total hour, if false, total hours=intervent + trip - pause hours"),
        'trip_require':fields.boolean('Trip', required=False),
        'trip_hour': fields.float('Trip hour', digits=(16, 6)),
        'break_require':fields.boolean('Break', required=False, help='If intervention is split in 2 part for break'),
        'break_hour': fields.float('Break hour', digits=(16, 6), help='Duration of break'),
        'intervention_request': fields.text('Intervention request'),
        'intervention': fields.text('Intervention description'),
        'internal_note': fields.text('Internal note'),        
        'type_id':fields.many2one('intervention.type', 'Type', required=False),
        'sector_id':fields.many2one('intervention.sector', 'Sector', required=False),
        'user_id':fields.many2one('res.users', 'User', required=True),
        'tipology':fields.selection([
            ('work','Lavorativo'), # Pay
            ('extra','Extra Lavorativo'), 
            ('personal','Personale'),], 'Tipology', help='If the invervention is about work, or extra work but usefull to plann appointment', select=True, readonly=False),            
        'mode':fields.selection([
            ('phone','Phone'),
            ('customer','Customer address'),
            ('connection','Tele assistence'),
            ('company','Company address'),],'Mode', select=True, readonly=False),
        'state':fields.selection([
            ('draft', 'Appointment draft'),
            ('waiting', 'Appointment awaiting confirmation'),
            ('confirmed', 'Appointment confirmed'),
            ('cancel', 'Appointment cancelled'),
            ('close', 'Appointment executed'),            
            ('reported', 'Appointment executed reported'),            
        ],'State', select=True, readonly=True),
    }
    _defaults = {
        'state': lambda *a: 'draft',
        'user_id': lambda obj, cr, uid, context: uid,
        'tipology': lambda *x: 'work',
        'manual_total': lambda *x: False,
    }    
    def intervention_draft(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'draft', }) 
        return True

    def intervention_waiting(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'waiting', }) 
        return True

    def intervention_confirmed(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'confirmed', }) 
        return True

    def intervention_cancel(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'cancel', })
        return True

    def intervention_close(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'close', })
        return True

    def intervention_report_close(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'reported', })
        return True        
intervention_report()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
