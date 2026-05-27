{
    'name': 'Heredar Fechas Landed Cost y Ajuste de Inventario',
    'version': '1.0',
    'category': 'Extra Tools',
    'description': """
    Este modulo tiene la funcion de heredar fechas al modelo de valoracion de stocky sus dependencias""",
    'summary': 'Heredar Fechas en la Creacion de un landed cost o ajuste de inventario',
    'sequence': '10',
    'author': 'Sodigitalim',
    'maintainer': 'soluciones digitales para el comercio internacional',
    'depends': ['sale', 'purchase', 'stock', 'stock_landed_costs', 'base'],
    'data': [
        'security/group_inherit_date.xml',
        'view/view.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}