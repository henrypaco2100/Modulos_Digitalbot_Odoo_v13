# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Cancelar Punto de Venta',
    'version': '1.0',
    'summary': 'Modulo cancelar pedido',
    'description': 'Modulo para cancelar punto de ventas',
    'category': 'Punto de venta',
    'author': 'Sodigitalim Principal',
    'depends': ['base', 'mail', 'point_of_sale', 'account', 'stock', 'sd_stock_valuation_layer', 'stock_picking_cancel_extended'],
    'data': [
        "views/inherit_pos_order.xml",
        "views/inherit_pos_order_button.xml",
        "security/pos_cancel_order_security.xml"
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}