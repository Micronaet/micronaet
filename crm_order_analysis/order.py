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


# Utility:
def Prepare(valore):
    # For problems: input win output ubuntu; trim extra spaces
    # valore=valore.decode('ISO-8859-1')
    valore = valore.decode('cp1252')
    valore = valore.encode('utf-8')
    return valore.strip()


def PrepareDate(valore):
    if valore:  # TODO test correct date format
       return valore
    else:
       return time.strftime("%d/%m/%Y")


def PrepareFloat(valore):
    valore=valore.strip()
    if valore: # TODO test correct date format
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values


class etl_order_line(osv.osv):
    """ List of document lines used for analysis in partner view
    """
    _name = 'etl.order.line'
    _order ='name'

    _columns = {
        'name': fields.char('Number', size=10, required=True, readonly=False),
        'date': fields.date('Date', help="Date when order is created"),
        'deadline': fields.date(
            'Deadline', help="Deadline for statistic evaluation of delivery"),
        # 'amount': fields.float('Total amount', digits=(16, 2)),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', required=False),
        'product_id': fields.many2one(
            'product.product', 'Product', required=False),
        'chemical_category_id': fields.related(
            'product_id', 'chemical_category_id', type='many2one',
            relation="chemical.product.category", string='Category',
            readonly=True, store=True),

        'quantity': fields.float(
            'Total amount', digits=(16, 2)),  # TODO serve?
        'note': fields.text('Note'),

        'total': fields.float('Total amount', digits=(16, 2)),
        'delivered': fields.float('Total delivered', digits=(16, 2)),
        'expected': fields.float('Total expected', digits=(16, 2)),
        'left': fields.float('Total left', digits=(16, 2)),
        'state':fields.selection([
            ('ok', 'OK'),
            ('ko', 'KO'),
            ('borderline', 'Border line'),
            ('unknow', 'Unknow period'),
        ], 'State', select=True, readonly=False),
    }
etl_order_line()


class etl_order(osv.osv):
    """ List of document lines used for analysis in partner view
    """
    _name = 'etl.order'
    _order = 'date,name'

    # Scheduled action: #######################################################
    def schedule_etl_order_import(
            self, cr, uid, path, file_name, header_filename, context=None):
        """ ETL operations for import partner order in OpenERP
            (parameter setted up in scheduled action for file name)
            In this scheduled action there also importation for movement in
            general account like BC or FT (only invoice lines)
        """
        import logging, os, csv
        from datetime import datetime, timedelta

        _logger = logging.getLogger('crm_order_analysis')

        partner_proxy = self.pool.get("res.partner")
        order_line_proxy = self.pool.get("etl.order.line")
        product_proxy = self.pool.get('product.product')
        partner_proxy = self.pool.get('res.partner')

        total_order_id = {}  # for next importation
        counter = {'tot': 0, 'upd': 0, 'err': 0, 'err_upd': 0, 'new': 0}

        # Import BC e FT according to order line: *****************************
        delete_all = self.unlink(cr, uid, self.search(cr, uid, []))
        # clean all DB

        # Import order:
        year_now = datetime.now().year
        for year in [year_now, year_now - 1, year_now - 2]:
            try:
                file_complete = os.path.expanduser(
                    os.path.join(path, "%s%s" % (year, file_name)))
                lines = csv.reader(open(file_complete, 'rb'), delimiter=";")
                tot_colonne = 0
                for line in lines:
                    if counter['tot'] < 0:  # jump n lines of header
                       counter['tot'] += 1
                    else:
                       if not tot_colonne:
                           tot_colonne=len(line)
                           _logger.info('Start sync of documents lines year %s [cols=%s, file=%s]'%(year, tot_colonne, file_name))

                       if len(line): # jump empty lines
                           if tot_colonne != len(line): # tot # of colums must be equal to # of column in first line
                               _logger.error('Colums not the same')
                               continue

                           counter['tot']+=1
                           csv_id=0
                           acronym = Prepare(line[csv_id])
                           csv_id+=1
                           number = Prepare(line[csv_id])
                           csv_id+=1
                           order = Prepare(line[csv_id])
                           csv_id+=1
                           product_id = Prepare(line[csv_id])
                           csv_id+=1
                           # descrizione aggiuntiva
                           csv_id+=1
                           unit = PrepareFloat(line[csv_id])
                           csv_id+=1
                           amount = PrepareFloat(line[csv_id])
                           csv_id+=1
                           date = Prepare(line[csv_id])
                           csv_id+=1
                           partner_id = Prepare(line[csv_id])

                           # calculated fields:
                           name = "%s-%s-%s"%(acronym, year, number)
                           date = "%s-%s-%s"%(date[:4],date[4:6],date[-2:]) if date else False
                           year_analysis=date[:4] if date else False


                           product_id = product_proxy.search(cr, uid, [('default_code','=',product_id)])
                           if product_id:
                               product_id = product_id[0]
                           else:
                               product_id = False

                           partner_id = partner_proxy.search(cr, uid, [('mexal_c','=',partner_id)])
                           if partner_id:
                               partner_id = partner_id[0]
                           else:
                               partner_id = False

                           # Total for update in next importation
                           if (order,product_id) not in total_order_id:
                               total_order_id[(order,product_id)] = amount or 0.0
                           else:
                               total_order_id[(order,product_id)] += amount or 0.0

                           data_line = {
                                        'name': name,
                                        'type': acronym,
                                        'date': date,
                                        'year': year_analysis,
                                        'product_id': product_id,
                                        'partner_id': partner_id,
                                        'quantity': unit,
                                        'unit': amount / unit if unit!=0.0 else 0.0,
                                        'amount': amount,
                                        'order': order,
                                       }
                           new_id=self.create(cr, uid, data_line)
                _logger.info('End import movement lines year %s, total: [%s]'%(year, counter['tot']))
            except:
                _logger.error('Error generic import movement lines year %s, total: [%s]'%(year, counter['tot']))

        counter = {'tot':0,'upd':0, 'err':0, 'err_upd':0, 'new':0}

        # Import etl.order.line **********************************************
        delete_all=order_line_proxy.unlink(cr, uid, order_line_proxy.search(cr, uid, [])) # clean all DB

        try: # test error during importation:
            file_complete = os.path.expanduser(os.path.join(path, header_filename))
            lines = csv.reader(open(file_complete,'rb'), delimiter = ";")
            tot_colonne=0
            for line in lines:
                if counter['tot'] < 0:  # jump n lines of header
                   counter['tot'] += 1
                else:
                   if not tot_colonne:
                       tot_colonne=len(line)
                       _logger.info('Start sync of order header [cols=%s, file=%s]'%(tot_colonne, header_filename))

                   if len(line): # jump empty lines
                       if tot_colonne != len(line): # tot # of colums must be equal to # of column in first line
                           _logger.error('Order file: Colums not the same')
                           continue

                       counter['tot']+=1
                       csv_id=0
                       partner_code = Prepare(line[csv_id])      # ref customer
                       csv_id+=1
                       #                                      Description partner
                       csv_id+=1
                       order = Prepare(line[csv_id])         # num order
                       csv_id+=1
                       date = Prepare(line[csv_id])         # date
                       csv_id+=1
                       deadline = Prepare(line[csv_id])     # deadline
                       csv_id+=1
                       default_code = Prepare(line[csv_id]) # ref product
                       csv_id+=1
                       #                                      product name
                       csv_id+=1
                       quantity = PrepareFloat(line[csv_id])     # quantity
                       csv_id+=1
                       line_state = Prepare(line[csv_id])        # state
                       csv_id+=1
                       note = Prepare(line[csv_id])         # note
                       csv_id+=1

                       # get product:
                       product_id = product_proxy.search(cr, uid, [('default_code','=',default_code)])
                       if product_id:
                           product_id = product_id[0]
                       else:
                           product_id = False

                       # get partner:
                       partner_id = partner_proxy.search(cr, uid, [('mexal_c','=',partner_code)])
                       if partner_id:
                           partner_id = partner_id[0]
                       else:
                           partner_id = False

                       # calculated fields:
                       date = "%s-%s-%s"%(date[:4],date[4:6],date[-2:]) if date else False
                       deadline = "%s-%s-%s"%(deadline[:4],deadline[4:6],deadline[-2:]) if deadline else False

                       # statistic calculation:
                       delivered = (total_order_id[(order,product_id)] if (order,product_id) in total_order_id else 0.0)
                       total = quantity + delivered

                       now_quantity=0.0
                       if date and deadline:
                           now_date = datetime.strptime(datetime.now().strftime("%Y-%m-%d"),"%Y-%m-%d") #datetime.now()
                           from_date = datetime.strptime(date, "%Y-%m-%d")
                           to_date = datetime.strptime(deadline, "%Y-%m-%d")
                           interval= (to_date - from_date).days
                           now_interval = (now_date - from_date).days
                           now_quantity = total * now_interval / interval
                           if now_quantity > quantity:
                               state='ok'
                           else:
                               state='ko'
                           # TODO borderline status to evaluate in perc. !!!!
                       else:
                           state='unknow'    # no from / to period so no statistics

                       data = {
                               'name': order,
                               'partner_id': partner_id,
                               'quantity': quantity,
                               'date': date,
                               'deadline': deadline,
                               'product_id': product_id,
                               'note': note,
                               'total': total,     # Total order
                               'delivered': delivered,
                               'expected': now_quantity,     # Total order
                               'left': quantity,   # To delivery (order value)
                               'state': state,        # 3 state value depend on period valutation
                              }
                       create_order_id = order_line_proxy.create(cr, uid, data)

            _logger.info('End import order headers %s, total: [%s]'%(year, counter['tot']))
        except:
            _logger.error('Error generic import order headers, total: [%s]'%(counter['tot']))

        return

    _columns = {
                'name': fields.char('Document', size=15, help="Document-Year-Number"),
                'type':fields.selection([
                    ('BC','DDT'),
                    ('FT','Invoice'),
                    ('NC','Credit note'),
                    ('RC','Refund'),
                ],'Type', select=True, readonly=False),
                'year': fields.char('Year', size=4), #fields.date('Date'),
                'date': fields.date('Date'),
                'product_id': fields.many2one('product.product', 'Product'),
                'chemical_category_id': fields.related('product_id', 'chemical_category_id', type = 'many2one', relation = "chemical.product.category", string='Category', readonly = True, store = True),
                'partner_id': fields.many2one('res.partner', 'Partner'),
                'amount': fields.float('Total', digits=(16,2),),
                'unit': fields.float('Price unit.', digits=(16,2),),
                'quantity': fields.float('Q.', digits=(16,2),),
                # refer to order:
                'order': fields.char('Order number', size=15, help="Number of order that start the sale"),
    }
etl_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
