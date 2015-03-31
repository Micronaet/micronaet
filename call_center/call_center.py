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
import time

status_list=[('arrabbiato', 'Arrabbiato'),('non_interessato', 'Non interessato'), ('freddo','Freddo'), 
             ('indeciso', 'Indeciso'), ('convincibile','Convincibile'), ('interessato', 'Interessato'),
             ('caldo', 'Caldo')]

# inizializzo gli oggetti principali:
class callcenter_campaign(osv.osv):
    _name = 'callcenter.campaign'
    _description = 'Campaign'
callcenter_campaign()

class call_center_phone_call(osv.osv):
    _name = 'callcenter.phone'
    _description = 'Phone call'
call_center_phone_call()

class call_center_phone_product(osv.osv):
    _name = 'callcenter.phone.product'
    _description = 'Phone product'
    _rec_name = 'product_id'

    '''def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
            
        import pdb; pdb.set_trace()
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.product_id.name or name or "Non trovato"
        return res'''

    
    def _function_subtotal(self, cr, uid, ids, field_name, arg, context = None):
       ''' Calcola il prezzo subtotale per riga 
       '''
       res= {}
       for line in self.browse(cr, uid, ids, context=context):
           if line.simulazione:
              res[line.id]=(line.quantity or 0.0) * (line.product_id.standard_price or 0.0) * (100.0 - (line.discount or 0.0)) / 100.0
           else:
              res[line.id]=0.0
       return res
       
    _columns = {
        #'name':fields.char('Extra info', size=64, required=False, readonly=False),
        'product_id':fields.many2one('product.product', 'Prodotto', required=True),
        'phone_id':fields.many2one('callcenter.phone', 'Telefonata', required=False),        
        'simulazione':fields.boolean('Simulazione', required=False, help="Spuntando si simula l'acquisto per avere una prospettiva di costi"),
        'quantity': fields.integer('Quantity'),
        'discount': fields.float('Discount', digits=(16, 2)),
        'subtotal': fields.function(_function_subtotal, method=True, type='float', string='Subtotale', store=True),
        'note': fields.text('Note'),        
        # subtotal (conteggiando anche la spunta di simulazione)
    }
call_center_phone_product()

class call_center_phone_history(osv.osv):
    _name = 'callcenter.phone.history'
    _description = 'History'

    _columns = {
        'name' : fields.char('Impressioni', size=64, required=False, readonly=False,),
        'note': fields.text('Note'),
        'date': fields.datetime('Date'),
        'impression':fields.selection(status_list,'Impressione', select=True, readonly=False),
        'phone_id':fields.many2one('callcenter.phone', 'Telefonata', required=False),        
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
   
call_center_phone_history()

class call_center_phone_call(osv.osv):
    _name = 'callcenter.phone'
    _description = 'Phone call'
    _rec_name = 'partner_id'

    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def _function_subtotal(self, cr, uid, ids, field_name, arg, context = None):
       ''' Calcola il prezzo subtotale per riga 
       '''
       res= {}
       for line in self.browse(cr, uid, ids, context=context):
           total=0.0
           for product in line.product_ids:
               total+=product.subtotal or 0.0
           res[line.id]=total
       return res

    _columns = {
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'campaign_id':fields.many2one('callcenter.campaign', 'Campaign', required=False),
        'user_id':fields.many2one('res.users', 'Utente in carico', help="Utente che ha preso in carico la chiamata",required=False),
        'product_ids':fields.one2many('callcenter.phone.product', 'phone_id', 'Products', required=False),        
        'history_ids':fields.one2many('callcenter.phone.history', 'phone_id', 'History', required=False),        
        'impression':fields.selection(status_list,'Impressione generale del contatto', help="E' possibile poi particolareggiare nelle note la particolare telefonata, questa e' intesa per tutti i contati avuti col cliente", select=True, readonly=False),
        'note': fields.text('Annotazioni generali'),
        #TODO gruppo che dovrebbe fare la chiamata
        'date_charge': fields.datetime('Data presa in carico'),
        'date_recall': fields.datetime('Data richiamata'), # modifica ogni variazione
        'subtotal': fields.function(_function_subtotal, method=True, type='float', string='Subtotale', store=True),
        #TODO marcare il cliente come non contattare mai più? >> Registro delle opposizioni

        # Dati relativi alla campagna:
        'date_end_id': fields.related('campaign_id','date_end', type='datetime', string='Fine campagna'),
        'indicazioni': fields.related('campaign_id','indicazioni', type='text', string='Indicazioni'),
        
        'state':fields.selection([
            ('draft','Da fare'),
            ('incharge','Presa in carico'),
            ('richiamare','Richiamare'),
            ('vinta','Vinta'),
            ('persa','Persa'),            
        ],'State', select=True, readonly=True),
    }
    _defaults = {
        'state': lambda *a: 'draft',
        'user_id': lambda obj, cr, uid, context: uid,
    }

call_center_phone_call()

class callcenter_campaign(osv.osv):
    _name = 'callcenter.campaign'
    _inherit = 'callcenter.campaign'
    _description = 'Campaign'

    '''def intervention_draft(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state': 'draft', }) 
        return True'''

    _columns = {
        'name': fields.char('Description', size=64, required=False, readonly=False,),
        'indicazioni': fields.text('Indicazioni', help="Indicazioni di vendita che potrebbero essere utilizzate dal venditore"),
        'user_id': fields.many2one('res.users', 'Creatore', help="Utente che ha creato la campagna", required=False),
        'date_start': fields.datetime('Data inizio'), # modifica ogni variazione
        'date_end': fields.datetime('Data inizio'), # modifica ogni variazione        
        'patecipant_ids': fields.one2many('callcenter.phone', 'campaign_id', 'Partecipanti', required=False),
        
        # TODO gruppo di default
        'state':fields.selection([
            ('draft','Bozza'),
            ('partita','Partita'),
            ('chiusa','Chiusa'),            
        ],'State', select=True, readonly=True),
    }
    _defaults = {
        'state': lambda *a: 'draft',
        'user_id': lambda obj, cr, uid, context: uid,
    }
callcenter_campaign()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
