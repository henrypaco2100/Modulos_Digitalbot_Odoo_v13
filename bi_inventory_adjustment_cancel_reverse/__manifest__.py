# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': "Cancelar Ajuste de Inventario",
    'version': "13.0.0.2",
    'category': "Inventario",
    'summary': '',
    'description': """
    Cancela los Ajustes de inventario
    """,
    'author': "SODIGITALIM",
    'website' : "https://sodigitalim.com/",

    'depends': ['stock','sd_stock_valuation_layer'],
    'data': [
        "security/ir.model.access.csv",
        "security/inventory_adjustment_group.xml",
        "views/inventory_adjustment_view.xml"
    ],
    'qweb': [
    ],
    'auto_install': True,
    'installable': True,
}
