# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.
{
	'name': 'SD Empresa Merquimia',
	'version': '14.0',
	'summary': 'Dedicado Mejoras Para la Empresa Melquimia',
	'description': '''Modulo enfocado para Merquimia''',
    "price": 0,
    "currency": "",
	'author': 'Sodigitalim',
	'website': 'https://sodigitalint.com',
	'category': '',
	'depends': ['base','stock','sale','account'],
	'data': ['views/inherit_sale_order.xml',
			 'views/inherit_account_tax.xml','views/inherit_purchase_order.xml',
			   'views/inherit_res_user.xml','views/inherit_account_move.xml'],
	'installable': True,
	'application': True,
	'qweb': [
			],
    "images":['static/description/Banner.png'],
}
