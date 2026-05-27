{
    'name': 'Cancelar Ventas y Compras Automatizadas',
    'version': '13.0.0.2',
    'category': 'Venta y Compra',
    "author": "SODIGITALIM",
    "website": "https://sodigitalim.com/",
    'summary': 'Cancela las ventas y compras automatizadas',
    'description': """ 
    Cancelar Ventas y Compras
    """,
    'depends': ['sale_stock','stock_picking_cancel_extended','purchase','bi_inventory_adjustment_cancel_reverse','bi_automated_sale_order','bi_automated_purchase_order','sd_stock_valuation_layer'],
    'data': [
                'security/cancel_order_security.xml',
                'views/sale_view.xml',
                'views/purchase_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': True,
}
