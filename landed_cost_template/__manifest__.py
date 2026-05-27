# -*- coding: utf-8 -*-
# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Landed Cost Template for Additional Cost',
    'license': 'Other proprietary',
    'category': 'Operations/Inventory',
    'summary': 'Landed Cost Template for Additional Cost',
    'price': 15.0,
    'currency': 'EUR',
    'images': ['static/description/image.png'],
    'live_test_url': 'https://youtu.be/3gnTVDKYO70',
    'author' : 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'www.probuse.com',
    'version': '2.1.1',
    'description': """
Landed Cost Template for Additional Cost
""",
    'depends': ['stock_landed_costs'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/custom_landed_cost_wizard_view.xml',
        'views/landed_cost_template_view.xml',
        'views/stock_landed_cost_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
