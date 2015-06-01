#!/usr/bin/python
# -*- encoding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2002-2013 Micronaet S.r.l.
#                  (<http://www.micronaet.it>). All Rights Reserved
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
import imaplib

import pdb; pdb.set_trace()
# Parameters:
server = "server"
port = 993
username = "admin@example.com" 
password = "password"
inbox = "Inbox"

# Connection:
box = imaplib.IMAP4_SSL(server, port)
box.login(username, password)
box.select(inbox)

# Select all and delete:
typ, data = box.search(None, 'ALL')
i = 0
for num in data[0].split():
   box.store(num, '+FLAGS', '\\Deleted')
   print "Selezionato per eliminazione: ID%s" % num
box.expunge()
print "Eliminati"
box.close()
box.logout()
