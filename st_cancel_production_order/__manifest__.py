    # -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Cancelar Orden de Producción',
    'version': '13.0.0.2',
    'category': 'Manufacturing',
    "author": "SODIGITALIM",
    "website": "http://www.sodigitalint.com.bo",
    'summary': 'Cancelaciones de ordenes de produccion',
    'description': """
    """,
    'price': 0.0,
    'currency': "EUR",
    'depends': ['sale_stock','stock_picking_cancel_extended','purchase', 'mrp','bi_inventory_adjustment_cancel_reverse'],
    'data': [
                'security/cancel_production_security.xml',
                'views/production_order_cancell_all.xml',
    ],
    'live_test_url':'https://youtu.be/8fZri9yrwEM',
    'demo': [],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    "images":['static/description/Banner.png'],
}
