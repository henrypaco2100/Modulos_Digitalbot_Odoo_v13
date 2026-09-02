# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID


def _esi_recompute_pos_uom_metrics(cr):
    """Backfill base quantity/cost for POS lines already existing in the DB."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    Line = env['pos.order.line'].with_context(active_test=False)

    # ESI corrección: procesar en lotes para no cargar todo el histórico POS en RAM.
    last_id = 0
    while True:
        lines = Line.search([('id', '>', last_id)], order='id', limit=500)
        if not lines:
            break
        lines._compute_esi_uom_metrics()
        last_id = lines[-1].id


def post_init_hook(cr, registry):
    # ESI corrección: al instalar el módulo sobre una base con ventas antiguas,
    # recalcular inmediatamente las equivalencias UDM y el costo estimado.
    _esi_recompute_pos_uom_metrics(cr)
