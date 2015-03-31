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

class res_users_extra_fields(osv.osv):
    _name='res.users'
    _inherit ='res.users'

    _columns = {
               'mexal_id': fields.char('Mexal ID agente', size=9, required=False, readonly=False,help="Codice dell'Agente utilizzato in mexal, valido anche come riferimento per Supervisore e Responsabile"), 
                }
res_users_extra_fields()

class res_partner_panchemicals_fields(osv.osv):
    _name='res.partner'
    _inherit ='res.partner'

    _columns = {
               'import': fields.char('ID import', size=10, required=False, readonly=False),  
               'mexal_c': fields.char('Mexal cliente', size=9, required=False, readonly=False),
               'mexal_s': fields.char('Mexal fornitore', size=9, required=False, readonly=False),                         
               'fiscal_id_code': fields.char('Fiscal code', size=16, required=False, readonly=False),  
               'private': fields.boolean('Private', required=False),               # Private (not company)
               'type_cei': fields.char('Type CEI', size=1, required=False, readonly=False),  # Type of firm (CEE, Extra CEE, Intra CEE)

               # Agente, responsabile, supervisore (per presentare il solo codice:
               'mexal_resp': fields.char('Mexal responsabile', size=9, required=False, readonly=False), # Agente / utente interno alla ditta                        
               'responsible_name': fields.related('user_id','name', type='char', string='Responsible'), # Calculater: name of agent
               # NOTE: user_id (Agente/user for Openerp = responsible for Mexal 

               'mexal_age': fields.char('Mexal agente', size=9, required=False, readonly=False),        # Agente esterno alla ditta
               'mexal_age_description': fields.char('Mexal Agente desc.', size=60, required=False, readonly=False),        # Agente esterno alla ditta

               'mexal_super': fields.char('Mexal supervisore', size=9, required=False, readonly=False), # Agente / utente reponsabile
               'supervisor_id':fields.many2one('res.users', 'Supervisor user', required=False),

                }
res_partner_panchemicals_fields()

class res_partner_address_panchemicals_fields(osv.osv):
    _name='res.partner.address'
    _inherit ='res.partner.address'

    _columns = {
               'import': fields.char('ID import', size=10, required=False, readonly=False), 
               'mexal': fields.char('Codice Mexal', size=9, required=False, readonly=False), # Destinazione
               'mexal_c': fields.char('Mexal cliente', size=9, required=False, readonly=False),   
               'mexal_s': fields.char('Mexal fornitore', size=9, required=False, readonly=False),              
                }
res_partner_address_panchemicals_fields()

class res_partner_address_panchemicals_fields(osv.osv):
    _name='product.product'
    _inherit ='product.product'

    def _product_has_bom(sefl, cr, uid, product_id):
        '''Test if product has a bom with bom_id=false
        '''
        #import pdb; pdb.set_trace()
        cr.execute("SELECT id FROM mrp_bom WHERE product_id=%s and bom_id is null",(product_id,))
        list_bom=cr.fetchall()
        if list_bom:
           return list_bom[0][0] # return id TODO (only one?)
        else:   
           return False
           
    def _compute_recursive_price_bom(self, cr, uid, bom_id):
        '''Recursive function for calculate bom price:
           get id of mrp.bom
           loop on child recursive with id
           return only when bom record is a leave
        '''
        # 1. cerco il record bom
        bom_proxy=self.pool.get('mrp.bom').browse(cr, uid, bom_id)
        
        # 2. loop sui componenti: controllo se il prodotto ha una bom senza bom_id (semilavorato)
        tot=0
        for component in bom_proxy.bom_lines:                         
           has_bom= self._product_has_bom(cr, uid, component.product_id.id)
           if has_bom: # recurse:
              tot += component.product_qty * self._compute_recursive_price_bom(cr, uid, has_bom)
           else:
              if component.product_id.force_manual:
                 tot += component.product_qty * (component.product_id.manual_price or 0) # Segnalare l'errore?
              else:   
                 tot += component.product_qty * (component.product_id.standard_price or 0) # Segnalare l'errore?
        return tot
        
    def compute_price_from_bom(self, cr, uid, context=None):
        '''Procedura per calcolare il prezzo dei prodotti finiti in base
           al prezzo delle materie prime e della ricetta nella distinta 
           base, viene chiamato all'esterno appena finita l'importazione
           dei prodotti e ricette
        '''
        cr.execute("SELECT id, product_id FROM mrp_bom WHERE bom_id is null") 
        
        for item in cr.fetchall(): # loop for all bom without parent
            product_price = self._compute_recursive_price_bom(cr, uid, item[0])
            self.pool.get("product.product").write(cr, uid, item[1], {'standard_price': product_price}, context=context)
        return True

    def compute_price_from_bom_action(self, cr, uid, ids, context=None):
        '''Button event clicked from product.product form
        '''        
        from osv import osv
        
        self.compute_price_from_bom(cr, uid, context=context)
        raise osv.except_osv("Info", "Prezzi dei prodotti aggiornati!") # return??
        return True
        
    _columns = {
               'mexal_id': fields.char('Mexal cliente', size=16, required=False, readonly=False),   
               'import': fields.boolean('Imported', required=False), 
               'force_manual': fields.boolean('Force manual', required=False), 
               'manual_price': fields.float('Manual price', digits=(8,5), required=True,),                            
                }
                
    _defaults = {
                'mexal_id': lambda *x: False,
                'import': lambda *x: False,
                'force_manual': lambda *x: False,
                'manual_price': lambda *x: 0.0,
                }                            
res_partner_address_panchemicals_fields()

'''class mrp_bom_panchemicals_fields(osv.osv):

   _name = "mrp.bom" 
   _inherit = "mrp.bom" 
   
   def _bom_total_not_1_function(self, cr, uid, ids, args, field_list, context=None):
       if context is None: 
          context={}
        
       res = dict.fromkeys(ids, False)
       for bom in self.browse(self, cr, uid, ids):           
           tot=0.0
           for component in bom.bom_lines:
               tot += (component.product_qty or 0.0)
           res[bom.id]= (1.0 == tot)    
       return res
       
   _columns = {
              'bom_total_not_1': fields.function(_bom_total_not_1_function, method=True, type='boolean', string='Tot 1 test', store=True),              
              }
   
mrp_bom_panchemicals_fields()'''
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
