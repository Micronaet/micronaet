# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from tools.translate import _

# Product pricelist from model to generated:
class product_pricelist_generator(osv.osv_memory):
    """ Product pricelist generator 
        Copy an inactive pricelist creating a new pricelist with all product and
        calculate the price with actual pricelist rules
    """
    _name = "product.pricelist.generator"
    _description = "Product pricelist generator"

    _columns = {
        'pricelist_org_id':fields.many2one('product.pricelist', 'Original pricelist', required=True, help="Choose original pricelist used to calculate new complete pricelist/version"),
        'new':fields.boolean('New', required=False, help="Generate a new pricelist with this name"),
        'new_name': fields.char('New version name', size=64),
        'pricelist_des_id':fields.many2one('product.pricelist', 'Destination pricelist', required=False, help="If no new pricelist, use this pricelist to upgrade fields"),
    }

    _defaults = {
        'new': lambda *x: True,
    }

    '''def view_init(self, cr, uid, fields, context=None):
        idea_obj = self.pool.get('idea.idea')
        vote_obj = self.pool.get('idea.vote')

        for idea in idea_obj.browse(cr, uid, context.get('active_ids', []), context=context):

            for active_id in context.get('active_ids'):

                vote_ids = vote_obj.search(cr, uid, [('user_id', '=', uid), ('idea_id', '=', active_id)])
                vote_obj_id = vote_obj.browse(cr, uid, vote_ids)
                count = 0
                for vote in vote_obj_id:
                    count += 1

                user_limit = idea.vote_limit
                if  count >= user_limit:
                   raise osv.except_osv(_('Warning !'),_("You can not give Vote for this idea more than %s times") % (user_limit))

            if idea.state != 'open':
                raise osv.except_osv(_('Warning !'), _('Idea must be in "Open" state before vote for that idea.'))
        return False'''

    def do_create_update(self, cr, uid, ids, context=None):
        """
        Create or update pricelist
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of ids
        @return: Dictionary {}
        """
        
        if context is None:
           context={}
           
        wiz_browse = self.browse(cr, uid, ids[0], context=context)
        pricelist_ref_id = wiz_browse.pricelist_org_id.id
        if wiz_browse.new: # per ora facciamo questo
           if not wiz_browse.new_name: # TODO and duplicated!
              # TODO comunicate error!
              return {'type': 'ir.actions.act_window_close'}
              
           # Create new pricelist and pricelist version
           pricelist_id=self.pool.get('product.pricelist').create(cr, uid, {
                                                                            'name': wiz_browse.new_name, 
                                                                            'type': 'sale',
                                                                            # TODO currency 
                                                                           })
           if pricelist_id:
              version_id=self.pool.get('product.pricelist.version').create(cr, uid, {'name': "Versione: " + wiz_browse.new_name + " definitiva",
                                                                                     #'date_end': False, 
                                                                                     #'date_start': False, 
                                                                                     #'company_id': False, 
                                                                                     #'active': True, 
                                                                                     'pricelist_id': pricelist_id,
                                                                                    })
           else:
              pass # TODO comunicate error                                                                                 
        else:
           # Get pricelist and pricelist version            
           pricelist_id=0
           version_id=0
           
        if pricelist_id and version_id and wiz_browse.pricelist_org_id: # devono essere creati o trovati i listino/versione e deve esistere l'origine
           product_ids=self.pool.get('product.product').search(cr, uid, [('mexal_id', 'ilike', 'C')], context=context) # TODO write right filter
           for product in self.pool.get('product.product').read(cr, uid, product_ids, ['id', 'name', 'code',]):
               if product['code'][0:1].upper()=="C":
                  #import pdb; pdb.set_trace()
                  price_calc=self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_ref_id], product['id'], 1.0, False, {'uom': False, 'date': False,})[pricelist_ref_id]
                               
                  self.pool.get('product.pricelist.item').create(cr, uid, {'price_round': 0.00001, 
                                                                        'price_discount': 0.0, #0.052600000000000001, 
                                                                        #'base_pricelist_id': False, 
                                                                        'sequence': 200, 
                                                                        'price_max_margin': 0.0, 
                                                                        #'company_id': False, 
                                                                        #'product_tmpl_id': False, 
                                                                        'product_id': product['id'], 
                                                                        'base': 1, 
                                                                        'price_version_id': version_id, #[3, 'Rif. anno 2011'], 
                                                                        'min_quantity': 1, 
                                                                        'price_surcharge': price_calc,  # TODO Calcolare in funzione del listino
                                                                        #'price_min_margin': 0.0, 
                                                                        #'categ_id': False,
                                                                        'name': "[%s] %s"%(product['code'], product['name']),
                                                                        })
        else:
           pass # TODO comunicate error!
        return {'type': 'ir.actions.act_window_close'}
            
product_pricelist_generator()

# Product pricelist for customer:
class product_pricelist_customer(osv.osv_memory):
    """ Product pricelist generator for customers
    """
    _name = "product.pricelist.customer"
    _description = "Product pricelist customer"

    _columns = {
        'partner_id':fields.many2one('res.partner', 'Partner', required=True, help="Choose partner to create custom pricelist or add quotations"),
        'pricelist_id':fields.many2one('product.pricelist', 'Current pricelist', required=True, help="Choose original pricelist used to calculate new complete pricelist/version"),
        'comment': fields.char('Comment', size=64, help="Need to be created or updated"),        
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'price': fields.float('Price', digits=(16, 5)),
    }

    # on change function
    '''Create a new pricelist if not custom
       add custom price
       add old version as reference
    '''
    
    # event function
    def do_insert_quotation(self, cr, uid, ids, context=None):
       """
       Create or update pricelist if non custom and add personalization
       @param cr: the current row, from the database cursor,
       @param uid: the current user’s ID for security checks,
       @param ids: List of ids
       @return: Dictionary {}
       """
       
       if context is None:
          context={}
       import pdb; pdb.set_trace()   
       wiz_browse = self.browse(cr, uid, ids[0], context=context)        
       customer_proxy=self.pool.get('res.partner').browse(cr, uid, wiz_browse.partner_id.id) 
       pricelist_org_id = wiz_browse.pricelist_id.id # old pricelist set up
       pricelist_proxy=self.pool.get('product.pricelist').browse(cr, uid, pricelist_org_id)
        
       if not pricelist_proxy.customized: # Create customized and first rule
          pricelist_ref_id=self.pool.get('product.pricelist').create(cr, uid, {
                                                                                'name': "Personal: " + customer_proxy.name, 
                                                                                'type': 'sale',
                                                                                'customized': True,
                                                                                # TODO currency 
                                                                               })
          if pricelist_ref_id:
              version_ref_id=self.pool.get('product.pricelist.version').create(cr, uid, {'name': "From " + customer_proxy.property_product_pricelist.name,
                                                                                         #'date_end': False, 
                                                                                         #'date_start': False, 
                                                                                         #'company_id': False, 
                                                                                         #'active': True, 
                                                                                         'pricelist_id': pricelist_ref_id, #appena creato
                                                                                         })
          else:
              pass # TODO comunicate error                                                                                 
                                                                           
       else: # yet custom pricelist
          pricelist_ref_id = customer_proxy.property_product_pricelist.id 
          version_ref_id = customer_proxy.property_product_pricelist.version_id[0] # TODO take the first for now!
           
       if not (pricelist_ref_id and version_ref_id):
          # TODO comunicate error!
          return {'type': 'ir.actions.act_window_close'}
           
       pricelist_item_pool = self.pool.get('product.pricelist.item')
       # Creo l'ultima regola per prendere come riferimento il listino precedente
       rule_id = pricelist_item_pool.create(cr, uid, {'price_round': 0.00001, 
                                            'price_discount': 0.0, #0.052600000000000001, 
                                            'sequence': 500,  # ultima
                                            'price_max_margin': 0.0, 
                                            'base': 2,  # pricelist version
                                            'price_version_id': version_ref_id, #owner version
                                            'min_quantity': 1, 
                                            'price_surcharge': 0.0, 
                                            'base_pricelist_id': pricelist_ref_id,
                                            'name': "Listino rif: " + customer_proxy.property_product_pricelist.name,
                                            })
       # Creo la regola in base a prezzo e prodotto attuale
       # TODO cercare se esiste già!!!!!
       rule_id = pricelist_item_pool.create(cr, uid, {'price_round': 0.00001, 
                                            'price_discount': 0.0, #0.052600000000000001, 
                                            'sequence': 10, # tra le prime
                                            'price_max_margin': 0.0, 
                                            'product_id': wiz_browse.product_id.id, 
                                            'base': 1,
                                            'price_version_id': version_ref_id,
                                            'min_quantity': 1, 
                                            'price_surcharge': wiz_browse.price,
                                            'name': "[%s] %s"%(product['code'], product['name']),
                                            })
       # Set up partner with new pricelist                                     
       customer_proxy.write(cr, uid, [wiz_browse.partner_id.id], {'property_product_pricelist': pricelist_ref_id})
       #price_calc=self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_ref_id], product['id'], 1.0, False, {'uom': False, 'date': False,})[pricelist_ref_id]
       return {'type': 'ir.actions.act_window_close'}
            
product_pricelist_customer()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
