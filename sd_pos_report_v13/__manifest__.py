# -*- coding: utf-8 -*-
{
    'name': 'Mejoras POS Reporte v13',
    'version': '13.0.0.2',
    'summary': 'Mejoras al reporte de detalles de ventas POS, con filtro por sesiones',
    'category': 'Point of Sale',
    'author': 'SODIGITALIM',
    'website': 'https://sodigitalim.com/',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/pos_details_wizard.xml',
        'views/inherit_report_saledetail.xml',
    ],
    'installable': True,
    'application': False,
}
