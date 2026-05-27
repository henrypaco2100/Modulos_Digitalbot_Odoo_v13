# -*- coding: utf-8 -*-

{
    'name': 'Impresion de Reportes Precio Costo',
    'category': 'Accounting/Accounting',
    'summary': 'Reporte de Ventas Precio Costo',
    'version': '1.2',
    'description': """Imprima Reportes en Formato Excel o PDF de las ordenes de venta y todas sus dependencias""",
    'depends': ['sale'],
    'author': 'SODIGITALIM',
    'data': [
        'data/report_paperformat_horizontal.xml',
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/account_report_views.xml',
        'views/excel_report.xml',
        'report/account_product_pdf.xml'
            ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
