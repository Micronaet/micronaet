#!/usr/bin/python
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
import xmlrpclib
import ConfigParser
from datetime import datetime, timedelta
from Tkinter import *
import tkMessageBox


root = Tk()

# -----------------------------------------------------------------------------
#                                Utility function:
# -----------------------------------------------------------------------------

def center(win, width=400, height=300):
    win.update_idletasks()
    #width = width#win.winfo_width()
    #height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
#-------
# Event:
#-------

#def keypress(event):
#    print "Pressed:", repr(event.char)
    
#def mouse_left_click(event):
#    frame.focus_set()
#    print "Left Clicked at", event.x, event.y

#def mouse_right_click(event):
#    frame.focus_set()
#    print "Right Clicked at", event.x, event.y

#def quit():
#    if tkMessageBox.askokcancel("Quit", "Do you really wish to quit?"):
#        root.destroy()

def exit_click():
    root.destroy()
    
# Utility function:
def get_info():
    try:
        try:
            default_code = sys.argv[1]
        except:
            return "Errore utilizzare: lot_info.py CODICE_PRODOTTO"

        # ---------------------------------------------------------------------
        #                            Load access info
        # ---------------------------------------------------------------------
        config = ConfigParser.ConfigParser()
        config.read(['openerp.cfg'])
        dbname = config.get('dbaccess','dbname')
        user = config.get('dbaccess','user')
        pwd = config.get('dbaccess','pwd')
        server = config.get('dbaccess','server')
        port = config.get('dbaccess','port')  
        linux = eval(config.get('os', 'linux'))
        
        
        # ---------------------------------------------------------------------
        #                               Open socket
        # ---------------------------------------------------------------------
        sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common' % (
            server, port))
        uid = sock.login(dbname, user, pwd)
        sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (
            server, port))
                
        # ---------------------------------------------------------------------
        #                               Get info
        # ---------------------------------------------------------------------
        if linux: 
            eol = '\n'
        else:
            eol = '\r\n'
            
        product_ids = sock.execute(
            dbname, uid, pwd, 'product.product', 'search', [
                ('default_code', '=', default_code)]) 
        if product_ids:
            product_id = product_ids[0]
            lot_ids = sock.execute(
                dbname, uid, pwd, 'stock.production.lot', 'search', [
                    ('product_id','=',product_id)]) 
            lot_proxy = sock.execute(
                dbname, uid, pwd, 'stock.production.lot', 'read', lot_ids)
            info = "  Lotto                Data                          Q. rim." + eol

            total = 0.0
            for lot in lot_proxy:
                 total += lot['stock_available_chemical'] or 0.0
                 date = "%s-%s-%s" % (
                     lot['date'][8:10], 
                     lot['date'][5:7], 
                     lot['date'][:4]
                 ) if lot['date'] else "Non presente"
                 info += "%-20s%-20s%20.2f%s" % (
                     lot['name'], 
                     date, 
                     lot['stock_available_chemical'],
                     eol,
                 )   
            info += "                              Totale:   %20s%s" % (
                total, eol)

            return info
        return "Nessuna informazione"    
    except:
        return "Errore: %s" % (sys.exc_info(), )
        
#def smart_entry(parent, caption, width=None, **options):
#    Label(parent, text=caption).pack(side=LEFT)
#    entry = Entry(parent, **options)
#    if width:
#        entry.config(width=width)
#    entry.pack(side=LEFT)
#    return entry
    
# Set parent frame:
width = 650
height = 300
frame = Frame(root, width=width, height=height)

center(root, width=width, height=height)

#frame.bind("<Button-1>", mouse_left_click)
#frame.bind("<Button-3>", mouse_right_click)
#frame.bind("<Key>", keypress)

info_label = Label(root, text=get_info(), font=("Mono", 12))
info_label.pack(side=TOP)

exit = Button(frame, text="OK", command=exit_click)
exit.pack(side=BOTTOM)

frame.pack_propagate(0) # don't shrink
frame.pack()

# Edit box:
#password = Entry(root)
#password.pack()
#password.focus_set()

#user = makeentry(parent, "User name:", 10)
#password = smart_entry(root, "Password:", 10, show="*")
#company = smart_entry(root, "Company:", 10)


# Button
#info = Button(frame, text="Info", command=info_click)
#info.pack()



root.mainloop()
