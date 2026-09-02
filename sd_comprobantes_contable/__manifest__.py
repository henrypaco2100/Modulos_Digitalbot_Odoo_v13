# -*- coding: utf-8 -*-
{
    'name': 'Comprobantes Contables',
    'category': 'Contabilidad',
    'summary': 'Reportes Comprobantes contables',
    'version': '1.2',
    "author": "SODIGITALIM",
    "website": "http://www.sodigitalim.com",
    'description': """Reportes Comprobantes contables segun normas de Impuestos Nacional Bolivia""",
    # ESI correccion 2026-09-01:
    # El comprobante usa esi_cash_flow_id creado por bi_financial_pdf_reports.
    # bi_financial_excel_reports tambien forma parte de la solucion financiera ESI
    # y depende del modulo PDF. Se declaran ambos explicitamente para mantener
    # correcta la integracion solicitada.
    'depends': [
        'sale',
        'account',
        'bi_financial_pdf_reports',
        'bi_financial_excel_reports',
    ],
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
