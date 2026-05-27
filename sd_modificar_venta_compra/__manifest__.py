{
    'name': 'Modificar Venta y Compra',
    'version': '1.0',
    'category': 'Venta y Compra',
    'summary': '',
    'sequence': '10',
    'author': 'Sodigigalim',
    'maintainer': 'soluciones digitales para impulsar su Negocio',
    'depends': ['sale','purchase','bi_automated_purchase_order','bi_automated_sale_order'],
    'data': [
        'security/update_group_sale_purchase.xml',
        'view/inherit_order_purchase.xml',
        'view/inherit_order_sale.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}