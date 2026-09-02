# -*- coding: utf-8 -*-
{
    'name': 'Mejoras POS Reporte v13',
    'version': '13.0.0.5',
    'summary': 'Reporte POS por sesiones con vista previa, fecha, pago, PDF y Excel XLSX desde wizard o visor HTML',
    'category': 'Point of Sale',
    'author': 'SODIGITALIM',
    'website': 'https://sodigitalim.com/',
    'depends': ['base', 'web', 'point_of_sale'],
    'data': [
        'views/assets.xml',
        'views/pos_details_wizard.xml',
        'views/report_actions.xml',
        'views/inherit_report_saledetail.xml',
    ],
    # ESI corrección: plantilla QWeb del panel de botones del visor HTML.
    'qweb': [
        'static/src/xml/report_buttons.xml',
    ],
    'installable': True,
    'application': False,
}
