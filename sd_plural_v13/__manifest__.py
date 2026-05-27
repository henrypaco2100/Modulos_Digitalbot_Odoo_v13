# -*- coding: utf-8 -*-
{
    'name': "sd_plural_v13",

    'summary': """
        este modulo es la personalizacion de la empresa plural srl""",

    'description': """
        Se personalizaran cosas como verificar nit y copiar el ref a los apuntes desde los asientos
    """,

    'author': "SODIGITALIM",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sd_comprobantes_contable','mrp','base_multi_store'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'security/multi_store.xml',
        'data/secuencia_data.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/inherit_product_template.xml',
        'views/inherit_account_move.xml',
        'views/inherit_account_tax.xml',
        'views/inherit_res_partner.xml',
        'views/inherit_product_product.xml',
        'views/inherit_stock_move_line.xml',
        'views/inherit_stock_picking.xml',
        'views/inherit_mrp_production.xml',
        'wizard/stock_report_by_author.xml',
    ],
    'js': [

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
