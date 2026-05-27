# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'SD mejora compras',
    'version': '1.0',
    'summary': 'mejor del modulo de compra',
    'description': 'mejorar anadiendo el nombre del proovedor',
    'category': 'Compra',
    'authot': 'Sodigitalim',
    'depends': ['base','purchase'],
    'data': [
        "views/inherit_purchase_order.xml",
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}