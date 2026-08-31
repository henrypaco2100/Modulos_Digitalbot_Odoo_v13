# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PosDetailsWizard(models.TransientModel):
    _inherit = 'pos.details.wizard'

    session_ids = fields.Many2many(
        comodel_name='pos.session',
        relation='sd_pos_report_session_rel',
        column1='wizard_id',
        column2='session_id',
        string='Sesiones POS',
        help=(
            'Seleccione una o varias sesiones para limitar el reporte. '
            'Si no selecciona ninguna sesión, el reporte conserva el filtro '
            'estándar por fechas y puntos de venta.'
        ),
    )

    @api.onchange('pos_config_ids')
    def _onchange_pos_config_ids_sd_report(self):
        """Remove sessions that no longer belong to the selected POS configs."""
        if not self.session_ids:
            return
        if not self.pos_config_ids:
            self.session_ids = [(5, 0, 0)]
            return
        self.session_ids = self.session_ids.filtered(
            lambda session: session.config_id in self.pos_config_ids
        )

    def generate_report(self):
        """Pass the selected POS sessions to Odoo's native sale-details report."""
        self.ensure_one()
        data = {
            'date_start': self.start_date,
            'date_stop': self.end_date,
            'config_ids': self.pos_config_ids.ids,
            'session_ids': self.session_ids.ids,
        }
        return self.env.ref('point_of_sale.sale_details_report').report_action([], data=data)
