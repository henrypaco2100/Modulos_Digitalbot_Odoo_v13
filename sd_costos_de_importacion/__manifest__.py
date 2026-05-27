# -*- coding: utf-8 -*-

{
    'name': 'Automatizacion de Costes de Importacion en Landed Cost',
    'category': 'Inventory/Inventory',
    'summary': 'COSTOS DE IMPORTACION LC',
    'version': '1.0',
    "author": "SODIGITALIM",
    "website": "http://www.sodigitalim.com.bo",
    'description': """Se atomatizan los costes en destino de las compras de importacion generadas""",
    'depends': ['stock', 'sale_stock', 'stock_account','stock_landed_costs'],
    'data': [
        'views/stock_landed_cost_inherit_view.xml',
        'views/purchase_order_inherit_view.xml',
        'views/invoice_supplier_inherit_view.xml',
            ],
    "images": ['static/description/Sodigitalint.png'],
    'installable': True,
    'auto_install': False,
}
