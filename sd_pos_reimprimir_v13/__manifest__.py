# Copyright 2018 GRAP - Sylvain LE GAL
# Copyright 2018 Tecnativa S.L. - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Mejoras Pos Reimprimir Pedidp v13",
    "summary": "Administre pedidos antiguos de POS desde la interfaz",
    "version": "13.0.0.0.2",
    "category": "Punto de Venta",
    "author": "SODIGITALIM",
    "website": "https://sodigitalim.com/",
    "license": "AGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "views/assets.xml",
        "views/view_pos_config.xml",
        "views/view_pos_order.xml",
    ],
    "qweb": ["static/src/xml/pos.xml"],
    "application": False,
    "installable": True,
}
