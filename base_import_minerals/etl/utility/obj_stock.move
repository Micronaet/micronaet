origin ********************
		function _fnct_read
		digits [16, 2]
		fnct_inv _fnct_write
		func_method True
		fnct_inv_arg ['picking_id', 'origin']
		fnct_search _fnct_search
		func_obj stock.picking
		selectable True
		size 64
		type char
		store True
		string Origin
product_uos_qty ********************
		digits [16, 3]
		selectable True
		type float
		string Quantity (UOS)
address_id ********************
		domain []
		string Destination Address
		relation res.partner.address
		context {}
		selectable True
		type many2one
		help Optional address where goods are to be delivered, specifically used for allotment
create_date ********************
		selectable True
		type datetime
		readonly True
		select True
		string Creation Date
product_uom ********************
		domain []
		string Unit of Measure
		required True
		states {'done': [['readonly', True]]}
		relation product.uom
		context {}
		selectable True
		type many2one
price_unit ********************
		digits [16, 2]
		selectable True
		type float
		string Unit Price
		help Technical field used to record the product cost set by the user during a picking confirmation (when average price costing method is used)
procurements ********************
		domain []
		string Procurements
		relation procurement.order
		context {}
		selectable True
		type one2many
product_qty ********************
		digits [16, 3]
		string Quantity
		required True
		states {'done': [['readonly', True]]}
		selectable True
		type float
product_uos ********************
		domain []
		string Product UOS
		relation product.uom
		context {}
		selectable True
		type many2one
location_id ********************
		domain []
		string Source Location
		required True
		states {'done': [['readonly', True]]}
		relation stock.location
		context {}
		selectable True
		type many2one
		select True
		help Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations.
priority ********************
		selectable True
		selection [['0', 'Not urgent'], ['1', 'Urgent']]
		type selection
		string Priority
sale_line_id ********************
		domain []
		string Sales Order Line
		readonly True
		relation sale.order.line
		context {}
		selectable True
		type many2one
		select True
auto_validate ********************
		selectable True
		type boolean
		string Auto Validate
price_currency_id ********************
		domain []
		string Currency for average price
		relation res.currency
		context {}
		selectable True
		type many2one
		help Technical field used to record the currency chosen by the user during a picking confirmation (when average price costing method is used)
partner_id ********************
		function _fnct_read
		digits [16, 2]
		domain []
		fnct_inv _fnct_write
		func_method True
		fnct_inv_arg ['picking_id', 'address_id', 'partner_id']
		fnct_search _fnct_search
		relation res.partner
		store True
		context {}
		func_obj res.partner
		selectable True
		type many2one
		select True
		string Partner
company_id ********************
		domain []
		string Company
		required True
		relation res.company
		context {}
		selectable True
		type many2one
		select True
note ********************
		selectable True
		type text
		string Notes
state ********************
		selection [['draft', 'Draft'], ['waiting', 'Waiting'], ['confirmed', 'Not Available'], ['assigned', 'Available'], ['done', 'Done'], ['cancel', 'Cancelled']]
		string State
		readonly True
		selectable True
		type selection
		select True
		help When the stock move is created it is in the 'Draft' state.
 After that, it is set to 'Not Available' state if the scheduler did not find the products.
 When products are reserved it is set to 'Available'.
 When the picking is done the state is 'Done'.              
The state is 'Waiting' if the move is waiting for another one.
product_packaging ********************
		domain []
		string Packaging
		relation product.packaging
		context {}
		selectable True
		type many2one
		help It specifies attributes of packaging like type, quantity of packaging,etc.
move_history_ids ********************
		related_columns ['parent_id', 'child_id']
		string Move History (child moves)
		third_table stock_move_history_ids
		domain []
		relation stock.move
		context {}
		selectable True
		type many2many
date_expected ********************
		string Scheduled Date
		required True
		states {'done': [['readonly', True]]}
		selectable True
		type datetime
		select True
		help Scheduled date for the processing of this move
backorder_id ********************
		function _fnct_read
		digits [16, 2]
		domain []
		fnct_inv _fnct_write
		func_method True
		fnct_inv_arg ['picking_id', 'backorder_id']
		fnct_search _fnct_search
		relation stock.picking
		store False
		context {}
		func_obj stock.picking
		selectable True
		type many2one
		select True
		string Back Order
prodlot_id ********************
		domain []
		string Production Lot
		states {'done': [['readonly', True]]}
		relation stock.production.lot
		context {}
		selectable True
		type many2one
		select True
		help Production lot is used to put a serial number on the production
move_dest_id ********************
		domain []
		string Destination Move
		relation stock.move
		context {}
		selectable True
		type many2one
		select True
		help Optional: next stock move when chaining them
date ********************
		string Date
		required True
		readonly True
		selectable True
		type datetime
		select True
		help Move date: scheduled date until move is done, then date of actual move processing
scrapped ********************
		function _fnct_read
		digits [16, 2]
		fnct_inv _fnct_write
		func_method True
		fnct_inv_arg ['location_dest_id', 'scrap_location']
		readonly True
		fnct_search _fnct_search
		func_obj stock.location
		selectable True
		type boolean
		store False
		string Scrapped
name ********************
		string Name
		required True
		selectable True
		type char
		select True
		size 64
move_history_ids2 ********************
		related_columns ['child_id', 'parent_id']
		string Move History (parent moves)
		third_table stock_move_history_ids
		domain []
		relation stock.move
		context {}
		selectable True
		type many2many
product_id ********************
		domain [['type', '<>', 'service']]
		string Product
		required True
		states {'done': [['readonly', True]]}
		relation product.product
		context {}
		selectable True
		type many2one
		select True
location_dest_id ********************
		domain []
		string Destination Location
		required True
		states {'done': [['readonly', True]]}
		relation stock.location
		context {}
		selectable True
		type many2one
		select True
		help Location where the system will stock the finished products.
tracking_id ********************
		domain []
		string Pack
		states {'done': [['readonly', True]]}
		relation stock.tracking
		context {}
		selectable True
		type many2one
		select True
		help Logistical shipping unit: pallet, box, pack ...
picking_id ********************
		domain []
		string Reference
		states {'done': [['readonly', True]]}
		relation stock.picking
		context {}
		selectable True
		type many2one
		select True
