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

from openerp.osv import fields, osv

class wizard_browse_teeth(osv.osv_memory):
    """ Wizard for open URL """

    _name = "wizard.browse.teeth"
    _description = "Browse teeth"

    '''def view_init(self, cr, uid, fields, context=None):
        """
        This function checks for precondition before wizard executes
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param fields: List of fields for default value
        @param context: A standard dictionary for contextual values
        """
        if context is None:
           context = {}
        
        return {
            'type': 'ir.actions.act_url',
            'url': "http://www.micronaet.it",
            'target': 'new',
        }'''

    def do_browse_teeth(self, cr, uid, ids, context=None):
        """
        Create idea vote.
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Idea Post vote’s IDs.
        @return: Dictionary {}
        """
        if context is None:
           context = {}
        
        partner_id=context.get('partner_id', False)
        if partner_id:   
           url="http://192.168.100.51/denti.php?partner_id=%s"%(partner_id,)
        else:
           url="http://192.168.100.51/error.php" 
           
        #return {'type': 'ir.actions.act_window_close'}
        return {
        'type': 'ir.actions.act_url',
        'url': url,
        'target': 'new',
        }
    _columns = {
        'name':fields.char('Label', size=64, required=False, readonly=False), # never used!
    }
wizard_browse_teeth()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
