# -*- coding: utf-8 -*-
#!/usr/bin/python
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

# Parameters for calls (changeable):
pdf_path = "\\\\server0\\msds$"

# -----------------------------------------------------------------------------
#                                     Agent
# -----------------------------------------------------------------------------

if len(sys.argv) != 2: # No parameters exit
    sys.exit()

argument = sys.argv[1].split('//')[-1].split("/")

# -------------
# Calling case: 
# -------------
# MSDS:
if argument[0] == 'msds': # 2 arguments!
    os.system("start %s" % os.path.join(pdf_path, argument[1]))

# Other cases:
#elif    # for other call situations

# Wron calls:
else:
    pass    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

