# -*- coding: utf-8 -*-
{
    'name': 'Mejoras POS Reporte v13',
    'version': '13.0.0.11',
    'summary': 'Reporte POS Total / Precio-UDM / Total detallado con precisión decimal de Odoo',
    'category': 'Point of Sale',
    'author': 'ESI',
    'website': 'https://sodigitalim.com/',
    'depends': ['base', 'web', 'point_of_sale'],
    'data': [
        'views/assets.xml',
        'views/pos_details_wizard.xml',
        'views/pos_order_analysis_margin.xml',
        'views/report_actions.xml',
        'views/inherit_report_saledetail.xml',
    ],
    # ESI corrección: plantilla QWeb del panel de botones del visor HTML.
    'qweb': [
        'static/src/xml/report_buttons.xml',
    ],
    'installable': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
}
