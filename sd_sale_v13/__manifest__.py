# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'SD Mejoras Venta',
    'version' : '13.0.0.1',
    'summary': 'todas las mejorasa de sodigitalim para el modulo ventas',
    'sequence': 10,
    'description': """
    modificacion de la vista y modelo del modulo venta
    """,
    'category': 'sale',
    'website': 'https://sodigitalim.com/',
    'depends' : ['sale'],
    'data': [
        'views/inherit_sale_order.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
