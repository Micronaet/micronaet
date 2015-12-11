#!/usr/bin/python
# coding=utf-8
# Simply procedure for compare openerp modules with diff command
import os

old_path = "/home/thebrush/tmp/migrazione/micronaet60/coal_tax_exemption"
new_path = "/home/thebrush/lp7/micronaet/coal_tax_exemption"
module = "coal_tax_exemption"

from_file = [
    ('', 'coal.py'),
    ('', '__init__.py'),
    ('', '__openerp__.py'),
    ('', 'coal_dashboard.xml'),
    ('', 'coal_sequence.xml'),
    ('', 'coal_views.xml'),
    
    ('report', 'commercial_parser.py'),
    ('report', '__init__.py'),
    ('report', 'internal_parser.py'),
    ('report', 'parser.py'),
    ('report', 'parser_via_bf.py'),
    ('report', 'commercial_report.xml'),
    ('report', 'internal_report.xml'),
    ('report', 'via_bf_report.xml'),
    ('report', 'via_report.xml'),
    
    ('wizard', '__init__.py'),
    ('wizard', 'wizard_report.py'),
    ('wizard', 'wizard_report_view.xml'),
    
    ('security', 'coal_group.xml'),
    
    ('security', 'ir.model.access.csv'),    
    
]

#dif_file = os.path.expanduser(os.path.join("~", "module_diff.txt"))

for f in from_file:
    command = "diff %s %s > %s" % (
        os.path.join(old_path, *f),
        os.path.join(new_path, *f),
        os.path.join("~", "diff", module, "diff_%s_%s.txt" % (f[0], f[1]))
    ) 
    #print command
    os.system(command)
