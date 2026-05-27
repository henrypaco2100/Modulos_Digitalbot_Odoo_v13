# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

{
    'name': "Stock Forecast Report",
    'category': 'Stock',
    'version': '1.0',
    'author': 'Equick ERP',
    'description': """
        This Module allows you to generate Stock forecast Report PDF/XLS wise.
    """,
    'summary': """
        This Module allows you to generate Stock forecast Report PDF/XLS wise.
    """,
    'depends': ['base', 'purchase_stock','sale_stock','sale_management','account'],
    'license': 'AGPL-3',
    'website': "",
    'data': [
        'security/security.xml',
        'views/product_template_view.xml',
        'wizard/wizard_stock_forecast_view.xml',
        'report/report.xml',
        'report/stock_forecast_report_template.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: