#!/usr/bin/python
# -*- encoding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>)
#
###############################################################################
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################
# This script require installation of library xlrd:
#
# pip install xlrp --upgrade
# sudo easy_install openpyxl
#
# Call script passing file name (full path)
###############################################################################
from distutils.core import setup
import py2exe

setup(console=['convert.py'])

