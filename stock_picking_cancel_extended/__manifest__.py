# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name": "Cancelar las transferencias/reservas Stock",
    "version": "13.0.0.3",
    "author": "SODIGITALIM",
    'category': 'Inventario',
    "website": "https://sodigitalim.com/",
    'summary': 'Cancelar Transferencias',
    "depends": [
        "stock","sale_stock","sale_management","purchase",'sd_stock_valuation_layer',
    ],
    "demo": [],
    'description': """
        Cancelar las Transferencicas y Resevar en el modulo Inventario
    """,
    "data": [
        # "security/ir.model.access.csv",
        "security/picking_security.xml",
        "views/stock_view.xml"
    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "auto_install": False,
}
