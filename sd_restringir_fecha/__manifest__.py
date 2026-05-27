{
    'name': 'Restringir Fecha',
    'version': '1.0',
    'category': 'Extra Tools',
    'description': """
    Este modulo tiene la funcion de poder Restringir fecha 
    en una Orden de Venta, Compra, Transferencia y Facturas.""",
    'summary': 'Restringe Fechas en la Creacion de una Orden',
    'sequence': '10',
    'author': 'Sodigitalim',
    'maintainer': 'soluciones digitales para el comercio internacional',
    'depends': ['sale','purchase','stock','base'],
    'data': [
        'security/modify_date_security.xml',
        'view/view.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}