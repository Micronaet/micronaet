# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import openerp.netsvc as netsvc
import logging
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from import_function import *
import parse_function        


_logger = logging.getLogger(__name__)

# Generic function
def return_view(self, cr, uid, res_id, view_name):
    '''Function that return dict action for next step of the wizard
    '''
    view_element = view_name.split(".")
    views = []
    if len(view_element) == 2:
       model_id = self.pool.get('ir.model.data').search(cr, uid, [
           ('model', '=', 'ir.ui.view'),
           ('module', '=', view_element[0]),
           ('name', '=', view_element[1])])
       if model_id:
          view_id = self.pool.get('ir.model.data').read(
              cr, uid, model_id)[0]['res_id']
          views = [(view_id, 'tree'), (False, 'form')]

    return {
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'stock.picking', # object linked to the view
        'views': views,
        'domain': [('id', 'in', res_id)],
        #'views': [(view_id, 'form')],
        #'view_id': False,
        'type': 'ir.actions.act_window',
        #'target': 'new',
        'res_id': res_id,  # IDs selected
        # TODO domain for filter?
   }

class pickin_import_wizard(osv.osv_memory):
    ''' Wizard that load acutal csv file
        and ask "press button" to create
        pick in list (used for BF import)
    '''
    _name = "picking.import.wizard"

    # Utility funtion
    def preserve_window(self, cr, uid, ids, context=None):
        ''' Create action for return the same open wizard window
        '''
        view_id = self.pool.get('ir.ui.view').search(cr,uid,[
            ('model','=','picking.import.wizard'), 
            ('name','=','Wizard import picking from CSV'),
            ])

        return {
            'type': 'ir.actions.act_window',
            'name': "Import wizard",
            'res_model': 'picking.import.wizard',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'nodestroy': True,
        }

    def import_default_stock_location(self, cr, uid, context=None):
        ''' Load default stock location and return a tuple with his value
            return (in, out, internal, production)
        '''
        # TODO unificare con anagrafica carbone sempre delle location: stock.location.type 	
        location_proxy = self.pool.get('importation.default.location')
        return (
            location_proxy.get_location(cr, uid, 'supplier', context=context),
            location_proxy.get_location(cr, uid, 'customer', context=context),
            location_proxy.get_location(cr, uid, 'internal', context=context),
            )

    def import_or_test_loaded_files(self, cr, uid, ids, test, context=None):
        ''' This function has 2 mode:
            1) If test=True, the function try to read the files in wizard line
               verify some errors (no line, no lot, no hygro for coal, no partner
               and so on, if OK no error are returned
            2) If test=False, the function do the importation in the database
               return error and log informations
            Return value: (log_error, log_activity, record created (if 2)

            The return is befor natural end of function if is a locked error
        '''
        separator = ";"
        log_activity = "%s Start operation" % (datetime.now()) # TODO setup for errors
        log_error = ""
        pick_ids = [] # for final redirect
        date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            if_error = _('Error loading object')

            # create all used proxy reference:
            wizard_proxy = self.browse(cr, uid, ids)[0]
            wizard_line_pool = self.pool.get('picking.import.wizard.file') # in test, for update line
            importer_order_pool = self.pool.get('importation.purchase.order')
            partner_proxy = self.pool.get('res.partner')
            location_proxy = self.pool.get('importation.default.location')
            lot_proxy = self.pool.get('stock.production.lot')
            product_proxy = self.pool.get('product.product')
            move_proxy = self.pool.get('stock.move')
            picking_proxy = self.pool.get('stock.picking')
            picking_proxy_out = self.pool.get('stock.picking.out')
            picking_proxy_in = self.pool.get('stock.picking.in')

            # 3 default value for stock location (IN, OUT, INTERNAL)
            stock_in, stock_out, stock_internal = self.import_default_stock_location(
                cr, uid, context=context)
            if not (stock_in and stock_out and stock_internal): # locked error
               return (
                   "Need to setup default location for In, Internal, Production, Out before import! (Coal / Configuration / Stock location default)",
                   log_activity,
                   pick_ids, )

            # TODO IMPORTANTE VALUTARE I LOTTI IN INGRESSO PER CONTROLLARE SE IL PRODOTTO SIA COERENTE!!!!! <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            # TODO Ricordarsi anche la storicizzazione del numero lotto in base a OF
            direction_in = wizard_proxy.direction_in # IN o OUT
            
            if test: # Operations in test mode (verify if yet present): 
                if direction_in:  # if BF test double insert
                    # Test if there's some document present (partner-number-year)
                    for item_line in wizard_proxy.line_ids: # read all lines of wizard
                        full_name = item_line.full_name.split(" ")
                        year = full_name[-3]
                        partner_ref = full_name[-2]
                        ref = full_name[-1].split(".")[0]

                        partner_id = parse_function.get_partner_supplier(
                            self, cr, uid, partner_ref, direction_in)
                        if not partner_id:
                            continue # no partner, no document present
                            
                        domain = [
                            ('partner_id', '=', partner_id),
                            ('date', '>=', '%s-01-01 00:00:00' % (year)), 
                            ('date', '<=', '%s-12-31 23:59:59' % (year)),
                            ('type', '=', 'in'),
                            ('origin', 'ilike', '%s [%s' % (ref, '%')),
                        ]
                        BF_ids = picking_proxy.search(cr, uid, domain, context=context)
                        if BF_ids:
                            wizard_line_pool.write(cr, uid, item_line.id, {
                                'to_import': False,
                                'exist': True,
                                'log_error': 'Documento già presente in OpenERP!',
                                }, context=context)
                        
                else:  # if BC test double insert
                    history_line_ids = {}
                    for item_line in wizard_proxy.line_ids: # read all lines of wizard
                        # Test for duplicated exportation (ID and date are test)
                        not_import_lines = []
                        BC_id = item_line.import_document.split("/")[0]
                        if BC_id in history_line_ids: # yet present?
                            if item_line.date > history_line_ids[BC_id]['date']:
                                # save this parameter and not import previous
                                wizard_line_pool.write(cr,uid,history_line_ids[BC_id]['id'], {
                                    'to_import': False,
                                    'log_error': 'Documento duplicata (controllare la data per vedere quale tenere)!'}, context=context)
                                history_line_ids[BC_id]['id'] = item_line.id
                                history_line_ids[BC_id]['date'] = item_line.date
                            else:  # not import this
                                wizard_line_pool.write(cr,uid,item_line.id, {
                                    'to_import': False,
                                    'log_error': 'Documento duplicata (controllare la data per vedere quale tenere)!'}, context=context)

                        else: # Create element
                            history_line_ids[BC_id] = {}
                            history_line_ids[BC_id]['id'] = item_line.id
                            history_line_ids[BC_id]['date'] = item_line.date

            for file_item in wizard_proxy.line_ids: # all wizard line
                if not file_item.to_import: 
                   if file_item.exist: # delete file yet imported:
                       os.remove(file_item.full_name)
                       log_activity += "\n- Documento rimosso %s!" % (
                           file_item.name )
                   else:
                       log_activity += "\n- Documento saltato %s!" % (
                           file_item.name, )
                   continue # next file

                # Import document:
                if_error = _('Nessun %s CSV file, prego esportare il documenti prima e salvarlo in: %s' % (
                    file_item.name, 
                    file_item.path, ))
                lines = open(file_item.full_name, 'rb', )
                first = True

                if not lines:
                   update_line = wizard_line_pool.write(cr, uid, [file_item.id], {
                       'log_error': "Nessuna linea presente nel file:\n%s" % (
                           file_item.import_document),
                       'to_import': False,}, context=context)
                   continue # next line

                if_error = _('Errore leggendo / interpretando il file:\n%s' % (
                file_item.import_document))

                # Import file creatin stock.picking and stock.move (wit stock lot)
                line_ids_to_assigned = []
                for line_all in lines: # lines of file opened
                    line = line_all.replace('\x00', '').split(separator)

                    # CSV imported element (HEADER element):
                    ref = parse_function.prepare(line[0])                 # Pick ref.
                    date = parse_function.prepare_date(line[1])           # Date
                    partner_ref = parse_function.prepare(line[2])         # Partner code
                    partner = parse_function.prepare(line[3])             # Partner name
                    purchase_order = parse_function.prepare(line[8])      # Purchase order

                    # CSV imported element (LINE element):
                    product_ref = parse_function.prepare(line[4])         # Product code
                    um = parse_function.prepare(line[5])                  # UOM
                    #product_um = parse_function.prepare(line[5])         # Product UM
                    product_q = parse_function.prepare_float(line[6])     # Quantity
                    product_price = parse_function.prepare_float(line[7]) # Price
                    product_lot = parse_function.prepare(line[9])         # Lot (sometimes non present but get from openerp history)
                    hygro = parse_function.prepare_float(line[10])        # Hygro for coal

                    # calculed fields:
                    export_date=file_item.date[:10]

                    partner_id = parse_function.get_partner_supplier(self, cr, uid, partner_ref, direction_in)
                    if not partner_id: # update log for the line
                       update_line=wizard_line_pool.write(cr, uid, [file_item.id], {
                           'log_error': "Partner non trovato: %s - %s!" % (partner_ref, partner),
                           'to_import': False, }, context = context)
                       continue # next line

                    uom_id = parse_function.get_product_um(self, cr, uid, um)
                    if not uom_id: # update log for the line
                       update_line = wizard_line_pool.write(cr, uid, [file_item.id], {
                           'log_error': "U.M. non trovata: %s!" % (um),
                           'to_import': False, }, context = context)
                       continue # next line

                    product_id = parse_function.get_product(self, cr, uid, product_ref)  # Product ID from product_ref
                    if not product_id:
                        update_line = wizard_line_pool.write(cr, uid, [file_item.id], {
                            'log_error': "File: %s Errore non riesco ad abbinare prodotto al codice: %s!" % (
                                file_item.import_document, product_ref),
                            'to_import': False, }, context = context)
                        continue # next line

                    # test mandatory values (usually for coal product):
                    is_coal = is_product_coal(self, cr, uid, product_id, context=None)
                    if is_coal:
                        if not hygro and direction_in:  # hygro mandatory for coal (only in pickin in document)
                           update_line = wizard_line_pool.write(cr, uid, [file_item.id], {
                               'log_error': "Umidita' non presente ma obbligatoria per carboni: %s!" % (product_ref),
                               'to_import': False, }, context = context)
                           continue # next line

                        if not direction_in and not product_lot:  # on BC, mandatory lot
                           update_line = wizard_line_pool.write(cr, uid, [file_item.id], {
                               'log_error': "Obbligo del lotto per carbone in BC! Prodotto: %s!" % (product_ref),
                               'to_import': False, }, context = context)
                           continue # next line

                    try: # manage error during single file operation:
                        # stock.production.lot ********************************
                        if not direction_in: # BC *****************************
                            lot_id = False # TODO change for the future!

                            if product_lot:
                                lot_id = lot_proxy.search(cr, uid, [
                                    ('name', '=', product_lot)]) # TODO verify also the product
                                if lot_id: # not present: create?
                                    lot_control_proxy = lot_proxy.browse(cr, uid, lot_id[0]) # TODO verify also the product
                                    if lot_control_proxy.product_id and lot_control_proxy.product_id.id == product_id:
                                        lot_id = lot_id[0]  # use the first!
                                    else:
                                        update_line = wizard_line_pool.write(cr, uid, [file_item.id], {
                                            'log_error': "Lotto %s e' per il prodotto %s, attualmente nel doc. e': %s" % (
                                                product_lot,
                                                lot_control_proxy.product_id.name,
                                                product_ref),
                                            'to_import': False,}, context=context)
                                        continue # next line

                            if not lot_id and is_coal:
                                update_line = wizard_line_pool.write(cr, uid, [file_item.id], {
                                    'log_error': "Il lotto dovrebbe già essere presente ma non è stato trovato (BC con carbone), Lotto: '%s'! Prodotto: %s!" % (
                                        product_lot, product_ref),
                                    'to_import': False, }, context=context)
                                continue # next line
                            else: # lot not present:
                                pass # For now not mandatory lot for BC (only for coal)

                        else: # BF ********************************************
                            ### TODO import pdb; pdb.set_trace()
                            # -----------------
                            # Test product lot:
                            # -----------------
                            if product_lot: # lot number from import
                                lot_id = lot_proxy.search(cr, uid, [
                                    ('name', '=', product_lot)
                                ], context=context)

                                if lot_id: # Lot not found in system: create
                                    lot_id = lot_id[0] # take the first
                                else: # No creation, test for product
                                    # Create lot in OpenERP
                                    lot_id = lot_proxy.create(cr, uid, {
                                        'product_id': product_id,
                                        'name': product_lot,
                                        'stock_available': product_q,
                                        'date': date_now, #'2012-06-05 15:13:14',
                                    })
                                    
                                    # Create update lot importation history 
                                    importer_order_pool.new_lot(
                                        cr, uid, product_id, partner_id, 
                                        purchase_order, lot_id, 
                                        context = context)

                            else: # Lot number not from import (test in OpenERP history)
                                lot_id = importer_order_pool.check_lot(
                                    cr, uid, product_id, partner_id, 
                                    purchase_order, context=context)
                                if not lot_id:
                                    update_line = wizard_line_pool.write(cr, uid, [file_item.id], {
                                        'log_error': "Lotto vuoto e nessun precedente OF per questo prodotto: %s!" % (
                                            product_ref),
                                        'to_import': False,
                                    }, context=context)
                                    continue # next line

                            # Check if log get match with product_id on OpenERP (note: obviuosly correct for creation):
                            lot_control_proxy = lot_proxy.browse(
                                cr, uid, lot_id, context=context)
                            if not (lot_control_proxy.product_id and lot_control_proxy.product_id.id == product_id): # lot for another product
                                update_line = wizard_line_pool.write(
                                    cr, uid, [file_item.id], {
                                        'log_error': "Lotto %s e' per il prodotto %s, attualmente nel doc. e': %s" % (
                                            product_lot,
                                            lot_control_proxy.product_id.name if lot_control_proxy.product_id else "",
                                            product_ref),
                                        'to_import': False,
                                        }, context=context)
                                continue # next line
                    except:
                        update_line = wizard_line_pool.write(cr, uid, [file_item.id], {
                            'log_error': "Errore generico cercando analizzare il documento",
                            'to_import': False,}, context=context)
                        continue # next line  (doesn't create picking)


                    if first: # Aggiorno il wizard principale: **** PICKING HEADER *****
                       if_error = _('Error creating picking document:\n%s' % (file_item.import_document))
                       first=False

                       # Calculated fields  (this only for header)
                       #address_id = partner_proxy.address_get(cr, uid, partner_id).values()[0] # TODO verificare se sono più di uno
                       if not partner_id: # update log for the line
                          update_line=wizard_line_pool.write(cr, uid, [file_item.id], {
                              'log_error': "Indirizzo partner non trovato: %s - %s!" % (partner_ref, partner),
                              'to_import': False,}, context=context)
                          continue # next line

                       # stock.picking *****************************************
                       if not test: # create pick_id
                          picking_data = {
                              'origin': "%s [%s:%s]" % (
                                  ref, 
                                  "OF" if direction_in else "OC", 
                                  purchase_order),
                              #'name': sequence_pool.get(cr, uid, "stock.picking.in" if direction_in else "stock.picking.out") # or use picking_proxy different for out and in
                              #'name': 'IN/00001','stock_journal_id':,'invoice_state': ,
                              'date': date,
                              #'address_id': address_id,
                              'partner_id': partner_id,   # aggiunto dalla 7
                              'move_type': 'direct',
                              'type': 'in' if direction_in else 'out',
                              'note': 'Loaded from external program',
                              'state': 'done', # TODO test
                              'min_date': date,
                              'max_date': date,
                              'import_document': file_item.import_document,
                              #'import_date': export_date, # for registration

                              'wizard_id': wizard_proxy.id, # TODO togliere non serve, trovare il modo per il redirect finale
                          }

                          if not direction_in and is_coal: # assign XAB number
                              picking_data['xab_number'] = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out.xab')
                              _logger.info("XAB for BC created %s" % picking_data['xab_number'])

                          pick_id = picking_proxy.create(cr, uid, picking_data)
                          # NOTE: Below the part that generate "No XAB Number" in commercial report
                          #if direction_in:
                          #    pick_id = picking_proxy_in.create(cr, uid, picking_data)
                          #else:
                          #    pick_id = picking_proxy_out.create(cr, uid, picking_data) # Create XAB

                          if not pick_id:
                             wizard_line_pool.write(cr, uid, [file_item.id], {
                                 'log_error':"Errore creando documento di prelievo: %s (%s)!"%(ref, purchase_order),
                                 'to_import': False,}, context=context)
                             continue # next line
                          pick_ids.append(pick_id)
                       else: # test mode:
                           pick_id = 0
                    else: # not the first
                        pass

                    if_error = _('Errore creando i movimenti per il documento di carico / scarico: %s'%(file_item.name))

                    if not test: # create move, analysis, rename file
                        # stock.move ***********************************************
                        product_browse=product_proxy.browse(cr, uid, product_id)
                        data_move={
                            'product_uos_qty': product_q,
                            #'create_date': '2012-06-04 18:58:05', #'price_unit': 0.0,
                            'product_qty': product_q, #300.0,
                            'product_uos': product_browse.uos_id.id if product_browse.uos_id else False,
                            'product_uom': uom_id, #product_browse.uom_id.id if product_browse.uom_id else False, #[2, 'kg'],   <<< TODO devo caricarla come fa l'on_change!!
                            #'partner_id': [429, 'Luxalloys S.A.'],
                            'priority': '1',
                            #'sale_line_id': False,  'auto_validate': False, 'price_currency_id': False,
                            'location_id': stock_in if direction_in else stock_internal,           # depends on direction BF > comes from IN, BC > comes from INTERNAL
                            'location_dest_id': stock_internal if direction_in else stock_out,     # depends on direction BF > goes to INTERNAL, BC > goes to OUT
                            #'company_id': [1, 'Minerals & Metals spa'], 'note': False, 'state': 'done', 'product_packaging': False, 'purchase_line_id': False, 'move_history_ids': [],
                            'date_expected': export_date,
                            #'backorder_id': False,
                            #'move_dest_id': False,
                            'date': export_date,
                            #'production_id': False, 'is_coal': , 'scrapped': False, 'tracking_id': False, 'move_history_ids2': [],
                            'product_id': product_id,
                            'name': '[%s] %s'%(product_browse.code, product_browse.name),
                            'picking_id': pick_id,
                            'state': 'done',
                            'prodlot_id': lot_id,
                            'via_hygro': hygro, # TODO verify for VIA also in production (not override!!)
                        }
                        if direction_in and is_coal: # assign VIA number
                           data_move['via_number'] = self.pool.get('ir.sequence').get(cr, uid, 'product.coal')

                        # forse era stato tolto nella 6:
                        if not direction_in and is_coal: # assign XAB number
                           pass #data_move['xab_number']=self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out.xab')    # TODO debug

                        try:
                            pick_line_id=move_proxy.create(cr, uid, data_move, context=context)
                        except:
                           return ("Errore creando movimento: %s" % (data_move), log_activity, pick_ids)

                        if direction_in: # Create analysis for all new lot (starting from stock.picking:
                           picking_proxy.create_all_analysis(cr, uid, [pick_id], context=context) # TODO: better to put at the end of creation stock.picking (not for performance)
                           # TODO need to be logged better if did not create analysis!!

                        # move parsed files in history folder
                        os.rename(file_item.full_name, "%s%s.%s"%(file_item.path_history, pick_id, file_item.name[-3:]))
                        # TODO delete wizar line!
        except:
           # TODO if error in stock move, pick created without movements!!!!!!!!
           # TODO non viene comunicato: raise osv.except_osv(_('Error!'), _("Generic error during importation"))  # TODO test if works!
           return (if_error, log_activity, pick_ids) #wizard_raise_error(self, cr, uid, ids, if_error, log_activity, context=context)

        return (False, False, pick_ids) #Normal exit return no error stock.picking created

    def trigger_and_return(self, cr, uid, ids, trigger_signal, context=None):
        ''' Utility function: Object event for trigger event and leave open the window of wizard
        '''
        import openerp.netsvc

        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'picking.import.wizard', ids[0], trigger_signal, cr)

        return self.preserve_window(cr, uid, ids, context=context)

    # --------------------
    # Event button wizard:
    # --------------------
    def signal_import_load_object(self, cr, uid, ids, context=None):
        ''' Trigger event and return same window
        '''
        return self.trigger_and_return(cr, uid, ids, "signal_import_load", context=context)

    def signal_import_import_object(self, cr, uid, ids, context=None):
        ''' Trigger event and return same window
        '''
        return self.trigger_and_return(cr, uid, ids, "signal_import_import", context=context)

    # ----------------
    # Button Workflow:
    # ----------------
    def import_draft(self, cr, uid, ids, context=None):
        ''' First step of the wizard, present window ready to read files present
            in default folder
        '''

        # Verify some general parameters:
        error = False
        (stock_in, stock_out, stock_internal) = self.import_default_stock_location(cr, uid, context=context)

        if not (stock_in and stock_out and stock_internal):
           # need a configuration before proceed:
           error = "Need to setup default location for In, Internal, Production, Out before import! (Coal / Configuration / Stock location default)"

        # Start WF
        self.write(cr, uid, ids, {
            'state': 'draft',
            'error': error,
        })
        return True

    def import_loaded(self, cr, uid, ids, context=None):
        ''' Load file in default folder and create lines in wizard to manage
            importation, verify if the document is not present on DB
        '''
        if context is None:
           context = {}

        # Read filtered files in folder and create list of record to valuate in wizard
        load_file_2_field(self, cr, uid, ids, context=context)

        # Call import procedure in test mode:
        (log_error, log_activity, pick_ids) = self.import_or_test_loaded_files(cr, uid, ids, True, context=context)

        self.write(cr, uid, ids, {
            'state': 'loaded',
            'log_error': log_error,
            'log_activity': log_activity,
        })
        return True


    def import_imported(self, cr, uid, ids, context=None):
        ''' Import list of selected files in batch mode
            After redirected to list of picking document if succesfully
        '''

        if context is None:
           context = {}

        # Function:
        def wizard_raise_error(self, cr, uid, ids, error_message, log_activity, context=None):
           ''' Create fields with value and log error and go to imported state
           '''
           if context is None:
              context = {}

           self.write(cr, uid, ids, {
               # TODO or trigger to error state?
               'state': 'imported',
               'log_activity': log_activity,
               'error': error_message,
           }, context = context)
           #raise osv.except_osv(_('Error!'), _(error_message))  # NOTE: never comunicate!
           return True

        # Call import procedure not in test mode:
        (log_error, log_activity, pick_ids) = self.import_or_test_loaded_files(cr, uid, ids, False, context=context)

        # TODO note: no comunication of the error during wizard... use text box
        #if log_error: # roll back if log_error (only if log_error!)
        #   return wizard_raise_error(self, cr, uid, ids, log_error, log_activity, context=context)

        # Update state of WF, normale exit:
        self.write(cr, uid, ids, {
            'state': 'imported', # TODO or trigger to error state?
            'log_activity': log_activity,
            'log_error': log_error,
            'error': True if log_error else False,
        })
        return True

    def open_picking_tree(self, cr, uid, ids, context=None):
        """ Wizard button to redirect store.picking
        """
        if context is None:
           context = {}

        pick_ids = self.pool.get('stock.picking').search(cr, uid, [
            ('wizard_id','=',ids[0])])

        if pick_ids:
           return return_view(self, cr, uid, pick_ids, "stock.view_picking_in_tree")  # return created element in tree view:
        else:
           return {'type': 'ir.actions.act_window_close'}   # close

    _columns = {
        'name': fields.text('Importazione IN',),
        'name_out': fields.text('Importazione OUT',),
        'direction_in': fields.boolean('IN document?', help="If true the document is a picking in else, picking out", required=False),
        'error': fields.text('Error importing',),
        'log_activity': fields.text('Log activity',),
        'log_error': fields.text('Error', help="Error during operation"),
        'log_activity': fields.text('Log activity', help="Import activit log"),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('loaded', 'Loaded files'),
            ('imported', 'Imported document'),
        ], 'State', select=True, readonly=True),
        }

    _defaults = {
        'name': lambda *a: "Import BF document, precedently exported in CSV format and create a picking in document",
        'name_out': lambda *a: "Import BC document, precedently exported in CSV format and create a picking out document",
        'direction_in': lambda *a: True,
        'state': lambda *a: 'draft',
    }

class picking_import_wizard_file(osv.osv_memory):
    """ List of file to import read form file system
    """
    _name = 'picking.import.wizard.file'

    _columns = {
        'name': fields.char('File name', size=100, required=True, readonly=False),
        'path': fields.text('Path', help="Folder that contains no imported document"),
        'path_history': fields.text('History path', help="Folder that contains old imported document"),
        'full_name': fields.text('Full name', help="Full name of the file, according to file system syntax"),
        'to_import': fields.boolean('Import?', help="Is the file to import", required=False),
        'exist': fields.boolean('Exist?', help="If true then the file has already imported in DB", required=False),
        'date': fields.datetime('Export date', help="Export date of the file"),
        'import_document':fields.char('Document n.', size=18, required=False, readonly=False, help="Link to original imported document, format number/year ex.: 8015/2012"),
        'imported': fields.boolean('Imported', help="File is imported", required=False),

        'log_text': fields.text('Log', help="Log operation"),
        'log_error': fields.text('Error', help="Error during operation"),
        'log_activity': fields.text('Log activity', help="Import activit log"),

        'wizard_id': fields.many2one('picking.import.wizard', 'Wizard', required=False, on_delete='cascade'), # TODO put a counter
    }

    _defaults = {
        'exist': lambda *a: False,
    }

class pickin_import_wizard(osv.osv_memory):
    """ Extra fields 2many
    """
    _name = "picking.import.wizard"
    _inherit = "picking.import.wizard"

    _columns = {
       'line_ids': fields.one2many('picking.import.wizard.file', 'wizard_id', 'Files', required=False),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


