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

{
    'name': 'Acccounting Loan Management',
    'version': '1.0',
    'category': '',
    'description': """
        Manage partner loan
        """,
    'author': 'Micronaet S.r.l. - Nicola Riolini',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'analytic',
        ],
    'init_xml': [],
    'demo': [],
    'data': [
        'security/loan_group.xml',
        'security/ir.model.access.csv',
        
        'wizard/change_rate_view.xml',
        'loan_sequence.xml',        
        'loan_view.xml',        
        
        'workflow/loan_header_workflow.xml',
        'workflow/loan_rate_workflow.xml',
        ],
    'active': False,
    'installable': True,
    'auto_install': False,
    }
