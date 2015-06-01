#!/usr/bin/python
# coding=utf-8
# Simply procedure for compare openerp modules with diff command
import os

old_path = "/home/thebrush/tmp/migrazione/micronaet60/chemical_analysis"
new_path = "/home/thebrush/lp7/micronaet/chemical_analysis"

from_file = [
    ('', 'analysis.py'),
    ('', '__init__.py'),
    ('', '__openerp__.py'),
    ('', 'analysis_views.xml'),

    ('wizard', '__init__.py'),
    ('wizard', 'search_product.py'),
    ('wizard', 'search_product_view.xml'),

    ('security', 'ir.model.access.csv'),
    ('security', 'analysis_group.xml'),
]

for f in from_file:
    command = "diff %s %s > %s" % (
        os.path.join(old_path, *f),
        os.path.join(new_path, *f),
        os.path.join("~", "diff", "chemical_analysis", "diff_%s_%s.txt" % (f[0], f[1]))
    ) 
    #print command
    os.system(command)
