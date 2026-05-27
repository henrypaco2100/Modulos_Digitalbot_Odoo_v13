# -*- coding: utf-8 -*-

{
    'name': 'Sd Libro Compra y Venta v13',
    'category': 'Accounting/Accounting',
    'summary': 'Reporte de compra venta',
    'version': '1.2',
    'description': """Imprima Reportes en Formato Excel o PDF de libro de compra y venta""",
    'depends': ['account','base_multi_store'],
    'author': 'SODIGITALIM',
    'data': [
        'views/compras_iva.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_compra_venta.xml',
        'wizard/wizard_solo_compra.xml',
        'wizard/wizard_libro_compra_iva.xml',
        'views/menus_contabilidad.xml',
        'views/inherit_account_move.xml',
            ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
