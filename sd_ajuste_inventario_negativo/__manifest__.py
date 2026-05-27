# -*- coding: utf-8 -*-
{
    'name': 'Sd ajuste inventario no usar',
    'category': 'Inventory',
    'summary': 'Reporte de compra venta',
    'version': '1.2',
    'description': """Imprima Reportes en Formato Excel o PDF de libro de compra y venta""",
    'depends': ['stock'],
    'author': 'SODIGITALIM',
    'data': [
        'views/inherit_ajuste_inventario.xml',
        ],
    'installable': True,
    'auto_install': False,
    'application': True,
}