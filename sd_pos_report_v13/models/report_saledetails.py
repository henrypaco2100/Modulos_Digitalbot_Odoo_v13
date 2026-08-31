# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Extend Odoo 13's report bridge so the existing ``session_ids``
        argument of ``get_sale_details`` is actually used by the PDF report.
        """
        data = dict(data or {})

        configs = self.env['pos.config'].browse(data.get('config_ids', []))
        sessions = self.env['pos.session'].browse(data.get('session_ids', [])).exists()

        data['session_ids'] = sessions.ids
        data['session_names'] = sessions.mapped('name')

        # When sessions are explicitly selected, the native Odoo method uses
        # the complete selected sessions and does not apply the date filter.
        # Adjust the displayed date range so the report header is not misleading.
        if sessions:
            session_starts = [start for start in sessions.mapped('start_at') if start]
            session_stops = [stop or fields.Datetime.now() for stop in sessions.mapped('stop_at')]
            if session_starts:
                data['date_start'] = min(session_starts)
            if session_stops:
                data['date_stop'] = max(session_stops)
        data.update(self.get_sale_details(
            data.get('date_start'),
            data.get('date_stop'),
            configs.ids,
            sessions.ids,
        ))
        return data
