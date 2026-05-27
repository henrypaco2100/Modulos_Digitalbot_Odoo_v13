{
    'name': 'Devoluciones ',
    'version': '1.0',
    'category': 'Inventario',
    'description': '''
            Mejorar el modulo de Devoluciones para modificar la Venta, 
            Compra y asientos contables realizado por es movimiento "
         ''',
    'summary': 'Con este Modulo se podra realizar la "Factura Computarizada Bolivia',
    'sequence': '10',
    'author': 'Henry Paco Delgadillo',
    'maintainer': 'soluciones digitales para impulsar su negocio',
    'depends': ['sd_message_personalized','stock','account','sale','purchase'],
    'data': [
        'view/inherit_stock_return_views.xml',
        'wizard/message_wizard.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}