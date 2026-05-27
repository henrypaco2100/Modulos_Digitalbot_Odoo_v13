{
    'name': 'Heredar Fechas Compras',
    'version': '1.0',
    'category': 'Extra Tools',
    'description': """
    Este modulo tiene la funcion de heredar fechas al modelo de compras y sus dependencias""",
    'summary': 'Heredar Fechas en la Creacion de una compra cualquiera',
    'sequence': '10',
    'author': 'Sodigitalim',
    'maintainer': 'soluciones digitales para el comercio internacional',
    'depends': ['sale', 'purchase', 'stock', 'stock_landed_costs', 'base'],
    'data': [
        'security/group_inherit_date_purchase.xml',
        'view/inherit_button_date.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}