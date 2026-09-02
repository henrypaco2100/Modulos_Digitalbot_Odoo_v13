# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Recalculate old 13.0.0.7 cost values using the selected POS UOM."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    Line = env['pos.order.line'].with_context(active_test=False)

    last_id = 0
    while True:
        lines = Line.search([('id', '>', last_id)], order='id', limit=500)
        if not lines:
            break
        # ESI corrección: 2 cajas de 24 deben convertirse a 48 unidades antes
        # de multiplicar por standard_price.
        lines._compute_esi_uom_metrics()
        last_id = lines[-1].id
