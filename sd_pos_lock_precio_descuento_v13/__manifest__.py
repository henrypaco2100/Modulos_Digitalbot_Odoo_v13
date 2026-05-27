# -*- coding: utf-8 -*-

{
    'name': "Bloquear precio y descuento Punto de venta",
    'summary': """
        Bloquea los precios y descuento del punto de venta""",
    'description': """
        Este modulo añade nuevas funciones de bloqueo con contraseña del precio y descuento
    """,
    'author': "Sodigitalim Principal",
    'website': "",
    'category': 'Point Of Sale',
    'license': "LGPL-3",
    'version': '12.0.1.0',
    'images': ['static/description/icon.png'],
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/assets.xml',
        'views/pos_config_view.xml',
    ],
    'price': '0',
    'currency': 'EUR',
}
