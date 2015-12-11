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
from openerp.osv import osv, fields

class bank_movement_category(osv.osv):
    ''' List of document lines used for analysis in partner view
    '''    
    _name='bank.movement.category'
    _order ='name'
        
    _columns = {
                'name': fields.date('Categoria'),
                'note': fields.text('Note'),
                'parent_id': fields.many2one('bank.movement.category', 'Padre'), 
    }
    _defaults = {
        'parent_id': lambda *a: False,
    }
bank_movement_category()        

class bank_movement(osv.osv):
    ''' List of document lines used for analysis in partner view
    '''    
    _name='bank.movement'
    _order ='date'
    _rec_name = 'date'
        
    _columns = {
                'date': fields.date('Date'),
                'causale': fields.char('Causale', size=40),
                'anno': fields.integer('Anno'),
                'trimestre': fields.char('Trimestre'),
                'note_banca': fields.text('Note banca'),
                'note': fields.text('Note'),
                'dare': fields.float('Dare', digits=(16,2),),
                'avere': fields.float('Avere', digits=(16,2),),   

                'user_id': fields.many2one('res.users', 'Utente'),                
                'category_id': fields.many2one('bank.movement.category', 'Categoria'),                
    }
    
    #_defaults = {
    #            'user_id': lambda self, cr, uid, context: uid,
    #}
bank_movement()        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
