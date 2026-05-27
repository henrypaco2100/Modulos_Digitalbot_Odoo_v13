# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.
{
	'name': 'Automated Purchase Order Processing',
	'version': '14.0',
	'summary': 'Esta aplicacion ayuda a reducir el proceso de la orden de compra y hacerlo automatizado',
	'description': '''
	Compra automatica a la factura del proveedor procesamiento de la orden de compra automatica proceso de 
		compra automatica Procesamiento de la confirmacion de compra automatica flujo de trabajo automatico para 
		la orden de compra proceso automatico de la orden de compra flujo de trabajo automatico en la compra flujo 
		de trabajo automatico compra con un solo clic
	 ''',
    "price": 25,
    "currency": "EUR",
	'author': 'Sodigitalim',
	'website': 'https://sodigitalint.com',
	'category': 'Purchase',
	'depends': ['base','stock','purchase',],
	'data': [
		'security/ir.model.access.csv',
		'views/view_main.xml',
		'views/inherit_account_move_purchase.xml',
		'views/purchase_order_inherit.xml',
		],
	'installable': True,
	'application': True,
	'qweb': [
			],
    "images":['static/description/Banner.png'],
}
