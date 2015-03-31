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

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_objects':self.get_objects,
            'get_thousand_separator': self.get_thousand_separator,
        })

    def get_thousand_separator(self, value_int):
        ''' Format int in string with thousand separator
        '''
        import locale

        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        try:
            return "{0:n}".format(round(value_int,0)).replace(",",".")
        except:
            return "#ERR conv."    

    def get_objects(self, objects=None, wizard_data=None):
        ''' Generate loop elements:
            if comes from report return objects
            if comes from wizard return filtered objects        
        '''
        if wizard_data is None: 
            wizard_data = {}
            
        if not wizard_data.get('start', False):  # test if it comes from wizard
            return objects

        # Wizard part: *********************************************************        
        data_filter_domain = []

        if wizard_data:
            # get wizard data (if launched from there)
            from_date = wizard_data.get('from_date', False)
            to_date = wizard_data.get('to_date', False)
            
            if from_date:
                data_filter_domain = data_filter_domain + [('date_start','>=', "%s 00:00:00"%(from_date))]
            if to_date:
                data_filter_domain = data_filter_domain + [('date_start','<=', "%s 23:59:59"%(to_date))]

        production_pool = self.pool.get('mrp.production')
        line_ids = production_pool.search(self.cr, self.uid, data_filter_domain)
        return production_pool.browse(self.cr, self.uid, line_ids)
        


