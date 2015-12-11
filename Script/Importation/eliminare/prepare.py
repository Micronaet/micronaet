#!/usr/bin/python
# -*- coding: utf-8 -*-
import fields

# Parameters: ##################################################################
file_in = 'ordine.txt'            # Input file
file_out_mask = 'ordine.%s.txt'   # Mask for output files
max_field = 2046                  # Max num of char (+ 2 for \r\n)

# Code #########################################################################
# ---------
# Function: 
# ---------
def create_block(split_block, file_out_mask, tot):
    ''' Create new block with total and file
    '''
    position = len(split_block) + 1     # next ID key
    split_block[position] = (tot, open(file_out_mask%(position), "w"))
    return 

# ----------
# Main code: 
# ----------
split_block = {} # element with key (number of split): value ((tot field, file))
tot = 0

# Calculate split blocks
for item in fields.order: # all the field list (ordered as is)
    if tot + fields.field_order[item][0] > max_field:
        create_block(split_block, file_out_mask, tot)
        tot = fields.field_order[item][0]   # reset counter to current field length        
        print "Campo", item
    else:
        tot += fields.field_order[item][0]  # update counter with field length
create_block(split_block, file_out_mask, tot) # Create last block

# Verbose:
print "Totale caratteri dei vari blocchi:", sum([split_block[key][0] for key in split_block])
print split_block

# Split file depend on blocks
fin = open(file_in, "r")
for line in fin:
    from_position = 0
    for key in split_block: # loop on all split blocks
        to_position = from_position + split_block[key][0]
        split_block[key][1].write("%s\r\n"%(line[from_position:to_position],))
        from_position += split_block[key][0]
        
# close opened files
fin.close()                     # input
for key in split_block:         # all output
    split_block[key][1].close()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
