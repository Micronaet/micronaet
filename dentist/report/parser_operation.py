##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'group_list': self.get_line_list,
            'tooth_list': self.get_list,
        })

    def get_line_list(self, partner_id):
        ''' Calculate the list of lines group by product_code
        '''
        # Order and return a browse list:
        line_ids=self.pool.get('dentist.operation').search(self.cr, self.uid, [('partner_id', '=', partner_id),], order="tooth,date")
        return self.pool.get('dentist.operation').browse(self.cr, self.uid, line_ids)                
        
    def get_list(self, partner_id, side):        
        ''' Calculate array for dental posizion:  u(p) or d(own)
            at least 1 line is returned (for graphic rapresentation)
        '''
        from dental_schema import get_array_list
        return get_array_list(self, partner_id, side, False) 
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        
