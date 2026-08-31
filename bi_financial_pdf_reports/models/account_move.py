# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    esi_cash_flow_id = fields.Many2one(
        'esi.cash.flow',
        string='CTA Flujo',
        index=True,
        help='Clasificación del ingreso o egreso para el reporte de Flujo de Caja ESI.'
    )


class AccountMove(models.Model):
    _inherit = 'account.move'

    def post(self):
        """Propaga una CTA Flujo única hacia las líneas de Banco/Caja antes de contabilizar.

        Odoo 13 usa account.account.user_type_id.type == 'liquidity' para cuentas
        de Banco y Efectivo. Si el usuario clasificó una contrapartida y existe
        una sola CTA Flujo en el asiento, se copia a las líneas de liquidez vacías.
        Si existen varias CTA Flujo no se adivina la distribución; el usuario debe
        asignarlas manualmente en las líneas de Banco/Caja.
        """
        for move in self:
            flow_ids = move.line_ids.filtered(
                lambda l: l.esi_cash_flow_id and l.account_id.user_type_id.type != 'liquidity'
            ).mapped('esi_cash_flow_id')
            if len(flow_ids) == 1:
                liquidity_lines = move.line_ids.filtered(
                    lambda l: l.account_id.user_type_id.type == 'liquidity' and not l.esi_cash_flow_id
                )
                if liquidity_lines:
                    liquidity_lines.write({'esi_cash_flow_id': flow_ids.id})
        return super(AccountMove, self).post()
