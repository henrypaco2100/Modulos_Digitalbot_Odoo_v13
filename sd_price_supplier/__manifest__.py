    # -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Cotizaciones de Compras',
    'version': '13.0',
    'category': 'Purchase',
    "author": "SODIGITALINT",
    "website": "http://www.sodigitalint.com.bo",
    'summary': 'Procesos de Cotizaciones de Compras al proveedor de sus productos',
    'description': """
    """,
    'price': 0.0,
    'currency': "EUR",
    'depends': ['purchase'],
    'data': [
                'views/cost_supplier_view.xml',
                'security/ir.model.access.csv',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    "images": ['static/description/Banner.png'],
}
