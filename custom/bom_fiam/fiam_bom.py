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

class mrp_bom_fiam_fields(osv.osv):
    _name='mrp.bom'
    _inherit ='mrp.bom'
    _order = 'name,code'

    def get_bom_element_price(self, cr, uid, bom_id, context=None):
        ''' Procedura ricorsiva per calcolo prezzo distinta base 
            return total of sub bom_lines (recursive)
        '''        
        browse_bom_id = self.browse(cr, uid, bom_id) # un solo elemento!
        if browse_bom_id:
           if browse_bom_id.bom_lines:
              total = 0.0
              for item_bom_id in browse_bom_id.bom_lines:   
                  total += get_bom_element_price(self, cr, uid, item_bom_id.id, context=context) or 0.0                     
              return total
           else:
              return browse_bom_id.actual_total or 0.0 # uscita dalla ricorsione
        else:
           return 0.0
               
    #def compute_total_bom(self, cr, uid, ids, context=None): 
    #    ''' Funzione chiamata dal bottone in distinta base (per calcolare il 
    #        totale del prezzo bom
    #    '''
    #    return 

    def _get_fields_component(self, cr, uid, ids, args, field_list, context=None):
        ''' 1. Calcola il totale dei componenti presenti nella distinta base
            2. Verifica che il componente non sia stato indicato come obsoleto
            oppure controlla che la quotazione non sia più vecchia del 01/01 
            di due anni prima        
            3. Calcola il prezzo del componente (data minore o primo che trova)
               NB: dovrebbe esserci solo un fornitore
        '''
        res = {}
        riferimento = str(int(datetime.strftime(datetime.now(),"%Y"))-2) + "-01-01"
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = {}
            res[item.id]['tot_component'] = len(item.bom_lines)
            res[item.id]['old_cost'] = False
            res[item.id]['actual_price'] = 0.0
            res[item.id]['first_supplier'] = False
            price = 0.0
            date_max = False
            first_supplier = 0
            #is_active_price = False
            for seller in item.product_id.seller_ids:
                for pricelist in seller.pricelist_ids: # passo tutte le quotazioni a listino
                    if pricelist.is_active: 
                        if pricelist.date_quotation: # NOTE: 1 fornitore - 1 pl per 1 solo prezzo - tante date
                           # calcolo per il prezzo componente:
                           if date_max < pricelist.date_quotation: # cambio data e prezzo
                               date_max = pricelist.date_quotation
                               price = pricelist.price
                               first_supplier = (seller.name and seller.name.id) or False # nome fornitore
                               #is_active_price = pricelist.is_active
                        else: # data di quotazione vuota, prezzo presente
                           if not date_max: # solo nel caso non abbia ancora la data max prendo il prezzo
                               price = pricelist.price
                               first_supplier = (seller.name and seller.name.id) or False # nome fornitore
                               #is_active_price = pricelist.is_active
            # setto i valori finito il giro per fornitori              
            if date_max <= riferimento:  # ne basta una!
               res[item.id]['old_cost'] = True
            else:
               res[item.id]['old_cost'] = True
               
            res[item.id]['actual_price'] = price or 0.0
            res[item.id]['actual_total'] = (price or 0.0) * (item.product_qty or 0.0)
            res[item.id]['first_supplier'] = first_supplier            
            #res[item.id]['is_active_price'] = is_active_price
        return res

    _columns = {
                'product_qty': fields.float('Product Qty', digits=(8,5), required=True,),                 
                'obsolete': fields.boolean('Obsolete', required=False, help='Is better do not use this component!',),
                'note': fields.text('Note'),
                # Funziono per campi calcolati:
                'tot_component': fields.function(_get_fields_component, method=True, type='integer', string="Tot comp", store= True, multi=True), #store = {'idea.vote': (_get_idea_from_vote,['vote'],10)}),
                'old_cost': fields.function(_get_fields_component, method=True, type='boolean', string="Old price", store=True, multi=True),           
                'actual_price': fields.function(_get_fields_component, method=True, type='float', string="Price", digits=(8,5), store=False, multi = True,),
                'actual_total': fields.function(_get_fields_component, method=True, type='float', string="Subtotale", digits=(8,5), store=False, multi=True,),
                'first_supplier': fields.function(_get_fields_component, method=True, type='many2one', relation="res.partner", string="Primo forn.", store=False, multi=True,),                  
                #'is_active_price': fields.function(_get_fields_component, method=True, type='many2one', relation="res.partner", string="Primo forn.", store=False, multi=True,),
               }
               
    _defaults = {
                'obsolete': lambda *a: False,
                }
    
mrp_bom_fiam_fields()

class pricelist_partnerinfo_fiam_fields(osv.osv):
    _name='pricelist.partnerinfo'
    _inherit ='pricelist.partnerinfo'

    def _has_bom_funct(self, cr, uid, ids, args, field_list, context=None):
        res = dict.fromkeys(ids, False)        
        product_list=[]
        product_ids_convert={}
        # cerco l'elenco dei product_id da verificare
        for pricelist in self.browse(cr, uid, ids): 
            if (pricelist.product_id) and (pricelist.product_id.id not in product_list):
               product_list.append(str(pricelist.product_id.id))
               product_ids_convert[pricelist.product_id.id]=pricelist.id # usata per ricavare l'ids da product_id

        #("Resource(s) %s is(are) not member(s) of the project '%s' .") % (",".join(res_missing), project.name)
        #import pdb; pdb.set_trace()
        query="select distinct product_id from mrp_bom where product_id in (%s);"%(",".join(product_list))
        cr.execute(query) 

        for item_id in cr.fetchall():
            res[product_ids_convert[item_id[0]]]=True # Metto a vero solo quelli trovati
        return res

    _columns = {
        'is_active': fields.boolean("E' attivo", required=False, help="Spuntare solo la linea che ha l'ultimo prezzo attivo o da tenere evidenziato (es. posso spuntare l'ultimo prezzo per q.=1, e l'ultimo per q.=1000"),
        'date_quotation': fields.date('Date quotation'),
        'price': fields.float('Unit Price', required=True, digits=(8,5), help="This price will be considered as a price for the supplier UoM if any or the default Unit of Measure of the product otherwise"),
        'supplier_id': fields.related('suppinfo_id','name', type='many2one', relation='res.partner', string='Fornitore'),
        'product_id': fields.related('suppinfo_id','product_id', type='many2one', relation='product.template', string='Desc. prod./comp.', store=True),
        'product_supp_name': fields.related('suppinfo_id','product_name', type='char', size=128, string="Descrizione forn."),
        'product_supp_code': fields.related('suppinfo_id','product_code', type='char', size=64, string="Codice forn."),
        'product_name': fields.related('product_id', 'name', type='char', string='Desc. prod./comp.'), # to search text not in product form! 
        'uom_id': fields.related('product_id','uom_id', type='many2one', relation='product.uom', string='UM'),
        'has_bom': fields.function(_has_bom_funct, method=True, type='boolean', string="E' in distinta", store=False), 
    }    
    _defaults = {
        'is_active': lambda *a: True,
    }
pricelist_partnerinfo_fiam_fields()

class product_product_fiam_fields(osv.osv):
    _name='product.product'
    _inherit ='product.product'

    def _get_bom_ids_len(self, cr, uid, ids, args, field_list, context=None):
        res = dict.fromkeys(ids, 0)
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id]=len(product.bom_ids)
        return res

    def _get_first_supplier_funct(self, cr, uid, ids, args, field_list, context=None):
        res = {} #dict.fromkeys(ids, )
        for product in self.browse(cr, uid, ids, context=context):        
            res[product.id] = {}
            if product.seller_ids:               
               res[product.id]['first_code']=product.seller_ids[0].product_code
               res[product.id]['first_supplier']=product.seller_ids[0].name.id #.name.name
            else:
               res[product.id]['first_code']=''
               res[product.id]['first_supplier']=False               
        return res
        
    '''def _fnct_search_supplier_code(self, cr, uid, obj, name, args, context):    
        'Search in all supplier of a product if the code is present
        import pdb; pdb.set_trace()
        return True'''
        
    def _get_best_cost_funct(self, cr, uid, ids, args, field_list, context=None):
        res = dict.fromkeys(ids, 0)
        for product in self.browse(cr, uid, ids, context=context):
            prezzi=[]
            for seller in product.seller_ids: # get min price of list (for all supplier)
                for pricelist in seller.pricelist_ids:
                    if pricelist.is_active:
                       prezzi.append(pricelist.price)
            if prezzi:
               res[product.id]=min(prezzi)
            else:
               res[product.id]=0.0   
               
        return res

    _columns = {
                'best_cost': fields.function(_get_best_cost_funct, method=True, type='float', string='Best cost', store=False),
                'first_supplier': fields.function(_get_first_supplier_funct, method=True, type='many2one', relation='res.partner', string='Primo fornitore', store=True, multi='prima_fornitura'),
                'first_code': fields.function(_get_first_supplier_funct, method=True, type='char', size=64, string='Primo codice', store=True, multi='prima_fornitura',),
                'bom_len': fields.function(_get_bom_ids_len, method=True, type='integer', string='Tot. comp.', store=True),
    }    
product_product_fiam_fields()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
