##############################################################################
#
# Copyright (c) 2008-2011 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
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
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
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

from report import report_sxw
from report.report_sxw import rml_parse

stock_location={} # list of 4 location used in this parser

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'stock_move':self.stock_move,
        })

    def load_location(self):
        ''' Load 4 stock location once (used from 2 procedure)
        '''
        global stock_location
        
        type_location=('internal',
                       'in',
                       'out',
                       'production')
        for location in type_location:
            location_ids=self.pool.get('stock.location.type').search(self.cr, self.uid, [('name','=',location)])
            if location_ids:
               stock_location[location]=self.pool.get('stock.location.type').read(self.cr, self.uid, location_ids[0])['location_id'][0] # only the first (no duplication record
        
    def stock_move(self, wizard_data=None):
        ''' Filter only coal product (in state done)
            movement from in to production (+/-)
            wizard_data if the report is called from wizard
        '''
        
        global stock_location
        self.load_location()

        # Wizard filter (if present) *******************************************
        if wizard_data is None: 
            wizard_data={}
        
        data_filter_domain = []

        if wizard_data:            
            # get wizard data (if launched from there)
            from_date = wizard_data.get('from_date', False)
            to_date = wizard_data.get('to_date', False)
            start = wizard_data.get('start', 1)
            
            if from_date:
                data_filter_domain = data_filter_domain + [('date','>=', "%s 00:00:00"%(from_date))]
            if to_date:
                data_filter_domain = data_filter_domain + [('date','<=', "%s 23:59:59"%(to_date))]
        # **********************************************************************
        
        line_ids=self.pool.get('stock.move').search(self.cr, self.uid, data_filter_domain +  [('is_coal', '=', True),('state', '=', 'done'),
                                                                       ('location_id', '=', stock_location['internal']),
                                                                       ('location_dest_id', '=',  stock_location['production']),
                                                                       ], order="date")
        return self.pool.get('stock.move').browse(self.cr, self.uid, line_ids)                

