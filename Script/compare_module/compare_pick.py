#!/usr/bin/python
# coding=utf-8
# Simply procedure for compare openerp modules with diff command
import os

old_path = "/home/thebrush/tmp/migrazione/micronaet60/pickin_import"
new_path = "/home/thebrush/lp7/micronaet/pickin_import"

from_file = [
    ('', 'importation.py'),
    ('', '__init__.py'),
    ('', '__openerp__.py'),
    ('', 'importation_views.xml'),

    ('wizard', '__init__.py'),
    ('wizard', 'importation_wizard.py'),
    ('wizard', 'import_function.py'),
    ('wizard', 'parse_function.py'),
    ('wizard', 'import_workflow.xml'),
    ('wizard', 'view_wizard.xml'),

    ('security', 'ir.model.access.csv'),
]

for f in from_file:
    command = "diff %s %s > %s" % (
        os.path.join(old_path, *f),
        os.path.join(new_path, *f),
        os.path.join("~", "diff", "pickin_import", "diff_%s_%s.txt" % (f[0], f[1]))
    ) 
    #print command
    os.system(command)
