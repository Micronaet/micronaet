##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# Copyright (c) 2010-2011"Micronaet s.r.l.". (http://www.micronaet.it) 
#                    All Rights Reserved.
#                    General contacts <info@micronaet.it>
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

{
	"name": "Pricelist model partner product",
	"version": "1.0",
	"description": "Pricelist product for partner",
	"author": "Nicola Riolini - Micronaet s.r.l.",
    'website': 'http://www.micronaet.it',
	"depends": [
	    "base",
	    "sale",
        "pricelist_model",
        "partner_product_detail", # Micronaet/micronaet-mx (for price partic.)
    ],
	"category": "Custom/Pricelist",
	"init_xml": [],
	"demo_xml": [],
	"data": [
	    "security/pricelist_security.xml",
	    "security/ir.model.access.csv",
        "partner_view.xml", 
        "scheduler.xml",
        "report/customer_pricelist.xml",
        ],
	"installable": True
}
