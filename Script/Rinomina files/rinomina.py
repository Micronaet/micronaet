#!/usr/bin/python

import os
import glob

import pdb; pdb.set_trace()
for f in glob.glob("./*.jpg"):
    try:
        if f != f.lower():
            os.system("mv ./%s ./%s"%(f, f.lower()))
            print "Info    >>> mv ./%s ./%s"%(f, f.lcase())
        else:    
            print "Warning >>> mv ./%s ./%s"%(f, f.lower())
    except:
       print      "Error   >>> mv ./%s ./%s"%(f, f.lower())
            
