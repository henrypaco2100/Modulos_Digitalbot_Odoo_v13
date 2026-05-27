# -*- coding: utf-8 -*-

{
    'name': 'Reporte de Valoracion de Inventario',
    'category': 'Inventory/Inventory',
    'summary': 'Kardex Report',
    'version': '2.0',
    "author": "SODIGITALIM",
    "website": "http://www.sodigitalint.com.bo",
    'description': """Kardex Fisico Valorado de Inventario""",
    'depends': ['stock','stock_account'],
    'data': [
        'data/report_paperformat_horizontal.xml',
        'security/ir.model.access.csv',
        'security/security_groups.xml',
        'wizard/account_report_views.xml',
        'wizard/excel_report.xml',
        'wizard/saldo_producto.xml',
        'views/stock_move_line_inherit_view.xml',
        'views/inherit_stock_move.xml',
        #'views/tipes_moves_product_view.xml',
        # 'views/kardex_valuate_view.xml',
        # 'wizard/stock_quantity_history.xml',
            ],
    # 'qweb': ['static/src/xml/tree_view_button.xml'],
    "images": ['static/description/Sodigitalint.png'],
    'installable': True,
    'auto_install': False,
}
