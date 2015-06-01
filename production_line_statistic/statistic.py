# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from openerp.osv import osv, fields


class mrp_workcenter_motive(osv.osv):
    ''' List of motive, work and not work, for the line
    '''
    _name = 'mrp.workcenter.work.motive'
    _description = 'Workcenter work motive'
    _order = 'sequence, name'
    
    # -------------------------------------------------------------------------
    #                        Database
    # -------------------------------------------------------------------------
    _columns = {
        'sequence': fields.integer('Seq.'),
        'name': fields.char('Motive', size=64, required=True),
        'note': fields.text('Note'),
        'uptime': fields.boolean('Uptime', help='Motivation that means up time'),
    }
    _defaults = {
        'sequence': 100,
        'uptime': False,
    }

class mrp_workcenter_work(osv.osv):
    ''' WOrkcenter statistic (work and extra motives)
    '''
    _name = 'mrp.workcenter.work'
    _description = 'Workcenter work'
    _rec_name = 'workcenter_id'
    _order = 'date,workcenter_id'
    
    # -------------------------------------------------------------------------
    #                        Utility function
    # -------------------------------------------------------------------------
    def load_days_statistic(self, cr, uid, from_date, to_date, line=False, forced=False, context=None):
        ''' Load all statistic for range of date passed for all line (or line
            passed)
            If in a day there's no lavoration the day is considered not
            working except if forced
        '''
        domain = []

        # Get total per day:
        work_ids = self.search(cr, uid, [], context=context)
        statistic = {}
        for item in self.browse(cr, uid, work_ids, context=context):
            if item.date not in statistic:
                statistic[item.date] = {}
            if item.workcenter_id.id not in statistic[item.date]:
                statistic[item.date][item.workcenter.id] = [0.0, 0.0] # work, dont work
            if item.motive_id.work:
                statistic[item.date][item.workcenter.id][0] += item.hour
            else:
                statistic[item.date][item.workcenter.id][1] += item.hour
        
        
        wc_pool = self.pool.get('mrp.production.workcenter.line')
        wc_ids = wc_pool.search(cr, uid, domain, context=context)
        #for wc in wc_pool.browse(cr, uid, wc_ids, context=context):
        #    date = wc.real_date_planned[:10]
        #    work_ids = self.search(cr, uid, [
        #        ('workcenter_id', '=', wc.workcenter_id.id),
        #        ('date', '=', date),
        #        #('work', '=', True),
        #        ]
        #    remain_work = (wc.workcenter_id.max_hour_day or 16) - 
        #    for work in 
        #    if work_ids =     
        return 
    
    # -------------------------------------------------------------------------
    #                        Database
    # -------------------------------------------------------------------------
    _columns = {
        'workcenter_id':fields.many2one('mrp.workcenter', 'Line',
            required=True),
        'motive_id':fields.many2one('mrp.workcenter.work.motive', 'Motive'),
        'date': fields.date('Date'),
        'hour': fields.integer('Hour'),
        'work': fields.boolean('Work', help='If true the element if a working reason'),
    }
    
    _defaults = {
        'work': False,
    }



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
