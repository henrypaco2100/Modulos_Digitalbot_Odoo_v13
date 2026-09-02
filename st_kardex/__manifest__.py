# -*- coding: utf-8 -*-

{
    'name': 'Reporte de Valoracion de Inventario',
    'category': 'Inventory/Inventory',
    'summary': 'Kardex Report',
    'version': '13.0.2.1.0',
    'author': 'SODIGITALIM / mejoras ESI',
    'website': 'http://www.sodigitalint.com.bo',
    'description': 'Kardex Fisico Valorado de Inventario - Vista HTML, PDF, Excel y U.M. dinámicas',
    'depends': ['stock', 'stock_account'],
    'data': [
        'data/report_paperformat_horizontal.xml',
        'security/ir.model.access.csv',
        'security/security_groups.xml',
        'wizard/account_report_views.xml',
        'wizard/excel_report.xml',
        'wizard/saldo_producto.xml',
        'views/stock_move_line_inherit_view.xml',
        'views/inherit_stock_move.xml',
        'report/account_product_pdf.xml',
    ],
    'images': ['static/description/Sodigitalint.png'],
    'installable': True,
    'auto_install': False,
}
