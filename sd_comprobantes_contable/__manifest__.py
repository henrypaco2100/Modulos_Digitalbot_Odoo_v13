# -*- coding: utf-8 -*-

{
    'name': 'Comprobantes Contables',
    'category': 'Contabilidad',
    'summary': 'Reportes Comprobantes contables',
    'version': '1.1',
    "author": "SODIGITALIM",
    "website": "http://www.sodigitalim.com",
    'description': """Reportes Comprobantes contables segun normas de Impuestos Nacional Bolivia""",
    'depends': ['sale','account'],
    'data': [
        'security/security_groups.xml',
        'views/inherit_account_move.xml',
        'views/inherit_account_journal.xml',
        'report/report_comprobantes.xml',
        'report/report_account_move.xml',
        'report/report_account_payment.xml',
        'report/report_account_move_version_2.xml',
        'report/report_account_payment_version_2.xml',
    ],
    'installable': True,
    'auto_install': True,
    # "images":['static/description/digital2.png'],
}
