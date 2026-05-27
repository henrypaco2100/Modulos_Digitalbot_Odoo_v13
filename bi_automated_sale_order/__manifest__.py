# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.
{
	'name': 'Automated Sale Order Processing',
	'version': '13.0.0.7',
	'summary': 'Esta aplicacion ayuda a reducir el proceso de la orden de Venta y Automatizarlo',
	'description': '''
	odoo Orden de venta automatica Factura y confirmacion de entrega y procesamiento de ventas automaticas odoo
	odoo Ventas automáticas procesamiento de confirmación de entrega de facturas automático
	odoo Procesamiento automatizado de pedidos de venta Procesamiento automatizado de pedidos de venta odoo
	odoo Procesamiento de ventas automatizado Procesamiento de ventas automatizado odoo
	odoo orden de venta flujo de trabajo automático odoo orden de venta automatizada flujo de trabajo automático odoo
	odoo flujo de trabajo automático para órdenes de venta proceso automático de órdenes de venta proceso automático de órdenes de venta odoo
	odoo venta proceso automático venta proceso automático venta proceso automático odoo
	odoo ventas proceso automático ventas proceso automático ventas proceso automático odoo
	odoo proceso automático de pedidos de venta proceso automático de pedidos de venta proceso automático de pedidos de venta proceso automático odoo
	odoo orden de venta proceso automático orden de venta proceso automático orden de venta proceso automático odoo
	odoo proceso automático de órdenes de venta Procesamiento automático de órdenes de venta Procesamiento automático de órdenes de venta
	odoo procesamiento de ventas automático flujo de trabajo automático de procesamiento de ventas automático para pedidos de ventas
	odoo reducir el proceso de la orden de venta reducir el proceso de venta reducir el proceso de la orden de venta
	flujo de trabajo automático de odoo para órdenes de venta flujo de trabajo automático para órdenes de venta
	 ''',
    "price": 25,
    "currency": "EUR",
	'author': 'BrowseInfo',
	'website': 'http://www.browseinfo.in',
	'category': 'Sales',
	'depends': ['base','sale_management','stock','sale',],
	'data': [
		'security/ir.model.access.csv',
		'security/multi_automated_security.xml',
		'views/new_style.xml',
		'views/view_main.xml',
		'views/inherit_account_move.xml',
		'views/sale_order_inherit.xml',
		'views/inherit_res_user.xml',
		],
	'installable': True,
	'application': True,
	'live_test_url' :'https://youtu.be/vI1l11zbnik',
	'qweb': [
			],
    "images":['static/description/Banner.png'],
}
