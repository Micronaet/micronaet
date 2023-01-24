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
import os
import shutil
import ConfigParser
from library.posta import *   # utility for manage mail logs
from library import fields   # list and dict of fields


# Parameters: #################################################################
# Get the file:
cfg_file = "openerp.cfg"
config = ConfigParser.ConfigParser()
config.read([os.path.expanduser(os.path.join("~", cfg_file))])

# SMB parameters:
smb_path = config.get('smb', 'path')
#smb_user = config.get('smb','user'))
#smb_password = config.get('smb','password'))

# SMTP parameters:
smtp_server = config.get('smtp', 'server')
smtp_user = config.get('smtp', 'user')
smtp_password = config.get('smtp', 'password')
smtp_port = config.get('smtp', 'port')
smtp_destination = eval(config.get('smtp', 'destination'))
smtp_ssl_auth = eval(config.get('smtp', 'ssl'))
smtp_spa_auth = eval(config.get('smtp', 'spa'))

# Import parameters:
import_path_temp = config.get('import', 'path')
import_filename_temp = config.get('import', 'filename')
import_extension = config.get('import', 'extension').lower()
import_errorfile = config.get('import', 'errorfile')
import_logfile = config.get('import', 'logfile')
import_verbose = eval(config.get('import', 'verbose'))

file_out_mask = eval(config.get('import', 'file_out_mask'))
max_field = eval(config.get('import', 'max_field'))
import_command = eval(config.get('import', 'command'))

split_block = {} # element with key (number of split): value ((tot field, file))

# Utility function ############################################################
def import_init():
    global split_block

    def create_block(split_block, file_out_path, file_out_mask, tot):
        """ Create new block with total and file
        """
        position = len(split_block) + 1     # next ID key
        split_block[position] = (tot, open(os.path.join(file_out_path,file_out_mask % (position)), "w"))
        return

    # Calculate split blocks
    split_block = {}
    tot = 0

    for item in fields.order: # all the field list (ordered as is)
        if tot + fields.field_order[item][0] > max_field:
            create_block(split_block, import_path_temp, file_out_mask, tot)
            tot = fields.field_order[item][0]   # reset counter to current field length
            print "Campo", item
        else:
            tot += fields.field_order[item][0]  # update counter with field length
    create_block(split_block, import_path_temp, file_out_mask, tot) # Create last block

    # Verbose:
    print "Totale caratteri dei vari blocchi:", sum([split_block[key][0] for key in split_block])
    #print split_block

def split_file(file_in):
    """ Split file depend on blocks
    """
    global split_block

    fin = open(file_in, "r")
    for line in fin:
        from_position = 0
        for key in split_block: # loop on all split blocks
            to_position = from_position + split_block[key][0]
            split_block[key][1].write("%s\r\n" % (line[from_position : to_position], ), )
            from_position += split_block[key][0]

    # close opened files
    fin.close()                     # input
    for key in split_block:         # all output
        split_block[key][1].close()

def import_file(order_file, import_path_temp, import_filename_temp):
    """ Rename file, split and lauch importation
    """
    try:
        # Rename file in local order
        f_tmp = os.path.join(import_path_temp, import_filename_temp)
        shutil.copy(order_file, f_tmp)

        # Split file in 2 elements
        split_file(f_tmp)

        # Launch importation
        os.system(import_command)

        # Check importation error
        # TODO

        try:
            open(import_errorfile, "r")
            return False # there's some error
        except:
            # no error file
            pass # OK

        # History of the current file:
        order_file_history = os.path.join(import_path_temp, "history", os.path.basename(order_file))
        os.rename(order_file, order_file_history) # removed from FTP folder
        return True
    except:
        return "Error"

# TODO log operations
for file_name in os.listdir(smb_path):
    try:
        if file_name.split(".")[-1].lower() == import_extension:
            import_init()
            order_file = os.path.join(smb_path, file_name)
            res = import_file(order_file, import_path_temp ,import_filename_temp)
            if not res:
                print "ERR - [%s] Error importing file: %s! Import aborted till manually correct" % (order_file, res)
                break
            elif import_verbose:
                print "INFO - [%s] File imported!" % (order_file)

    except:
        print "ERR - %s Generic error" % ("Data e ora")

# TODO mail operations

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
