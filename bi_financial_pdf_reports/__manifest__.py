# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo All Financial Reports in PDF(BS,P&L,GL,Trial Balance) ',
    'version': '13.0.0.1',
    'author': 'Sodigitalim',
    'website': 'sodigitalim.com',
    'category': 'Contabilidad',
    'summary': 'Este complemento lo ayuda a imprimir todos los informes de contabilidad, es decir, hoja de balance, libro mayor, balance de comprobación, pérdidas y ganancias',
    'description': """ 
        Realizar reportes en pdf como el Balance General, Estado de Resultado y Libro Mayor con un formato modificable
    """,
    'depends':['account'],
    'data':[
        'views/account_financial_report_line.xml',
        # 'demo/account_financial_report_data.xml',
        'security/ir.model.access.csv',
        'views/account_financial_report_view.xml',
        'views/account_move_cash_flow_views.xml',
        'reports/financial_reports.xml',
        'reports/report_balancesheet.xml',
        'reports/report_balancesheet_personalizado.xml',
        'reports/report_balancesheet_v3.xml',
        'reports/report_estado_resultado.xml',
        'reports/report_estado_resultado_v3.xml',
        'reports/report_trialbalance.xml',
        'reports/report_generalledger.xml',
        'reports/report_generalledger_v2.xml',
        'reports/esi_cash_flow_report_templates.xml',
        'reports/esi_cash_flow_report_action.xml',
        'wizard/balancesheet_view.xml',
        'views/esi_cash_flow_views.xml',
        'views/financial_report_preview_views.xml',
        'wizard/profit_loss_view.xml',
        'wizard/trial_balance_view.xml',
        'wizard/general_ledger_view.xml',
        'wizard/esi_cash_flow_report_wizard_views.xml',

    ],
    'installable': True,
    'auto_install': True,
    'images':['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
