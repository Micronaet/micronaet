# /usr/bin/python
# -*- encoding: utf-8 -*-
# List field and first 5 element of table in argv
import os
import sys
import xmlrpclib
import ConfigParser


# -----------------------------------------------------------------------------
#                                Setup parameters
# -----------------------------------------------------------------------------
# Parameters:
cfg_file = os.path.expanduser(os.path.join(
    "~", "etl", "openerp", "openerp.cfg"))

operation_list = [
    'partner',          # 0. Import partner from MySQL DB
    'product',          # 1. Import product from MySQL DB
    'move_bs',          # 2. Import sql.move.line only BS
    'export_bs',        # 3. Export number of BS imported
    'import_q',         # 4. Import existence from accounting
    'compute_bs',       # 5. Compute existence from BS movements
    'export_q',         # 6. Export new Q from accounting (for orders)
    'move_all',         # 7. Import sql.move.line all without BS

    # before order:
    'export_inventory', # 8. Export inventory setted un OpenERP
    'import_inventory', # 9. Import inventory setted up in Accounting
    'set_commercial',   # 10. Import commercial information from customer
]

# Parameters from config file:
try:
    config = ConfigParser.ConfigParser()
    config.read([cfg_file])
    dbname=config.get('dbaccess','dbname')
    user=config.get('dbaccess','user')
    pwd=config.get('dbaccess','pwd')
    server=config.get('dbaccess','server')
    port=config.get('dbaccess','port')   # verify if it's necessary: getint
except:
    print "Cannot find openerp.cfg file in this folder!"
    sys.exit()

# -----------------------------------------------------------------------------
#                               Connection to OpenERP
# -----------------------------------------------------------------------------
try:
    sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common' % (
        server, port))
    uid = sock.login(dbname, user, pwd)
    sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (
        server, port), allow_none=True)
except:
    print "Cannot connect with OpenERP server!", sys.exc_info()
    sys.exit()

# -----------------------------------------------------------------------------
#                            Run request operation scheduled
# -----------------------------------------------------------------------------

try:
    # Test if there's correct extra parameters passed:
    operation = sys.argv[1]
    if operation not in operation_list:
        print "Operation not in list\n\n\tUse: python scheduler.py xxxx\n\t# xxxx is one of this operations: [%s]" % (operation_list)
        sys.exit()

    # -------------------------------------------------------------------------
    #                                Run scheduled
    # -------------------------------------------------------------------------
    if operation == operation_list[0]:      # 1. Import partner
        sock.execute(
            dbname, uid, pwd,
            "res.partner",
            'schedule_sql_partner_import')
        sock.execute(
            dbname, uid, pwd,
            "res.partner",
            'schedule_sql_partner_commercial_import')
        print "Partner imported!"

    elif operation == operation_list[1]:    # 2. Import product
        sock.execute(
            dbname, uid, pwd,
            "product.product",
            'schedule_sql_product_import')
        sock.execute(
            dbname, uid, pwd,
            "product.product",
            'schedule_sql_product_price_import')
        print "Product imported!"

    elif operation == operation_list[8]:    # Export inventory situation
        sock.execute(
            dbname, uid, pwd,
            "product.product",
            'update_inventory_quantity',
            ('~', 'etl', 'demo', 'inventory.txt'), )
        print "Import all movement (except BS) in OpenERP!"

    elif operation == operation_list[9]:    # Import inventory situation
        sock.execute(
            dbname, uid, pwd,
            "product.product",
            'update_inventory_quantity_status',
            ('~','etl','demo','cl.txt'), )
        print "Import all movement (except BS) in OpenERP!"


    elif operation == operation_list[2]:    # 3. Import movement BS line
        sock.execute(
            dbname, uid, pwd,
            "sql.move.line",
            'schedule_etl_move_line_import',
            0, 500, False, 0, (0, 0), 'BS')
        print "BS stock movement imported!"

    elif operation == operation_list[3]:    # 4. Send confirm of BS import
        sock.execute(
            dbname, uid, pwd,
            "sql.move.line",
            'send_bs_info_importation',
            '~/etl/demo', 'bs.txt')
        print "BS importation list exported!"

    elif operation == operation_list[4]:    # 5. Import existence accounting
        sock.execute(dbname, uid, pwd,
            "product.product",
            'import_quantity_existence_csv',
            '~/etl/demo', 'esi.txt')
        print "Accounting quantity imported!"

    elif operation == operation_list[5]:    # 6. Compute existence with BS
        sock.execute(
            dbname, uid, pwd,
            "product.product", 'update_bs_field')
        print "BS computation for each product executed!"

    elif operation == operation_list[6]:    # 7. Export existence from OpenERP
        sock.execute(
            dbname, uid, pwd,
            "product.product",
            'export_store_qty_csv',
            '~/etl/demo', 'store.txt')
        print "Export correct OpenERP quantity!"

    elif operation == operation_list[7]:    # 8. Import extra document (not BS)
        sock.execute(
            dbname, uid, pwd,
            "sql.move.line",
            'reimport_not_bs_document',
            ('OC', 'BC', 'FT', 'NC'))
        print "Import all movement (except BS) in OpenERP!"

    elif operation == operation_list[10]:    # 10. Set commercial
        sock.execute(
            dbname, uid, pwd,
            "res.partner",
            'schedule_sql_partner_commercial_import', )
        print "Import all movement (except BS) in OpenERP!"

except:
    print "Problem running operations!", sys.exc_info()
    sys.exit()
