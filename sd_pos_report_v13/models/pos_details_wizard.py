# -*- coding: utf-8 -*-

import base64
import io

import xlsxwriter

from odoo import api, fields, models, _


class PosDetailsWizard(models.TransientModel):
    _inherit = 'pos.details.wizard'

    # ESI corrección: filtro por una o varias sesiones POS.
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

    # ESI corrección: tres formas de presentar el mismo conjunto de ventas.
    # Totales = convierte a UDM base y consolida por producto.
    # Total - detallado = conserva la UDM de venta y consolida por producto + UDM.
    # Detallado = conserva cada línea con fecha y método de pago.
    report_type = fields.Selection(
        selection=[
            ('totals', 'Totales'),
            ('total_detailed', 'Total - detallado'),
            ('detailed', 'Detallado'),
        ],
        string='Tipo de reporte',
        required=True,
        default='totals',
        help=(
            'Totales: agrupa por producto y convierte todas las cantidades a la UDM base. '
            'Total - detallado: agrupa por producto y por la UDM realmente vendida, sin fecha ni método de pago. '
            'Detallado: muestra cada línea vendida con su fecha y método de pago.'
        ),
    )

    # ESI corrección: archivo temporal para descargar Excel directamente desde Odoo.
    excel_file = fields.Binary(string='Archivo Excel', readonly=True, attachment=False)
    excel_filename = fields.Char(string='Nombre archivo Excel', readonly=True)

    @api.onchange('pos_config_ids')
    def _onchange_pos_config_ids_sd_report(self):
        """Remove sessions that no longer belong to the selected POS configs."""
        # ESI corrección: al quitar un Punto de Venta también se limpian sesiones inválidas.
        if not self.session_ids:
            return
        if not self.pos_config_ids:
            self.session_ids = [(5, 0, 0)]
            return
        self.session_ids = self.session_ids.filtered(
            lambda session: session.config_id in self.pos_config_ids
        )

    def _sd_prepare_report_data(self):
        """Build one common data payload for HTML, PDF and Excel outputs."""
        self.ensure_one()
        return {
            'date_start': self.start_date,
            'date_stop': self.end_date,
            'config_ids': self.pos_config_ids.ids,
            'session_ids': self.session_ids.ids,
            'report_type': self.report_type or 'totals',
        }

    def action_view_report(self):
        """Open an HTML preview instead of forcing an immediate PDF download."""
        self.ensure_one()
        preview_data = self._sd_prepare_report_data()
        preview_data.update({
            'sd_pos_report_excel': True,
            'sd_pos_report_wizard_id': self.id,
        })
        return self.env.ref(
            'sd_pos_report_v13.sale_details_report_html'
        ).report_action([], data=preview_data)

    def generate_report(self):
        """Print the report as PDF using the exact same filters as the preview."""
        self.ensure_one()
        return self.env.ref('point_of_sale.sale_details_report').report_action(
            [], data=self._sd_prepare_report_data()
        )

    def action_export_xlsx(self):
        """Generate XLSX matching Totales / Total - detallado / Detallado."""
        self.ensure_one()

        # ESI corrección: HTML, PDF y Excel usan exactamente la misma lógica central.
        # Costo y ganancia se retiraron de Detalles de ventas y ahora se muestran
        # exclusivamente en Informes > Análisis de pedidos.
        report_data = self.env[
            'report.point_of_sale.report_saledetails'
        ]._get_report_values([], data=self._sd_prepare_report_data())

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'remove_timezone': True,
        })

        title_format = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'
        })
        subtitle_format = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter'
        })
        header_format = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center',
            'valign': 'vcenter', 'text_wrap': True,
        })
        text_format = workbook.add_format({'border': 1, 'valign': 'top'})
        qty_format = workbook.add_format({
            'border': 1, 'num_format': '#,##0.00', 'align': 'right'
        })
        money_format = workbook.add_format({
            'border': 1, 'num_format': '#,##0.00', 'align': 'right'
        })
        date_format = workbook.add_format({
            'border': 1, 'num_format': 'dd/mm/yyyy hh:mm:ss', 'align': 'center'
        })
        total_label_format = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'right'
        })
        total_money_format = workbook.add_format({
            'bold': True, 'border': 1, 'num_format': '#,##0.00', 'align': 'right'
        })

        report_type = report_data.get('report_type') or 'totals'
        is_totals = report_type == 'totals'
        is_total_detailed = report_type == 'total_detailed'

        if is_totals:
            sheet_name = _('Totales de ventas')
            headers = [_('Producto'), _('Cantidad'), _('U.M.'), _('Precio total')]
            widths = [48, 16, 18, 20]
        elif is_total_detailed:
            sheet_name = _('Total detallado')
            headers = [
                _('Producto'), _('Cantidad'), _('U.M.'),
                _('Precio Unitario'), _('Precio total'),
            ]
            widths = [42, 16, 18, 18, 20]
        else:
            sheet_name = _('Detalle de ventas')
            headers = [
                _('Producto'), _('Método de pago'), _('Fecha'), _('Cantidad'), _('U.M.'),
                _('Precio Unitario'), _('Precio total'),
            ]
            widths = [31, 20, 21, 13, 14, 17, 17]

        worksheet = workbook.add_worksheet(sheet_name[:31])

        last_col = len(headers) - 1
        for col, width in enumerate(widths):
            worksheet.set_column(col, col, width)

        worksheet.merge_range(0, 0, 0, last_col, _('Detalles de ventas POS'), title_format)
        worksheet.merge_range(
            1, 0, 1, last_col,
            report_data.get('company_name') or self.env.company.name,
            subtitle_format,
        )

        date_start = report_data.get('date_start')
        date_stop = report_data.get('date_stop')
        period_text = '%s - %s' % (
            fields.Datetime.to_string(date_start) if date_start else '',
            fields.Datetime.to_string(date_stop) if date_stop else '',
        )
        worksheet.merge_range(2, 0, 2, last_col, period_text, subtitle_format)

        row = 3
        worksheet.merge_range(
            row, 0, row, last_col,
            _('Tipo de reporte: %s') % report_data.get('report_type_label', ''),
            subtitle_format,
        )
        pos_names = report_data.get('config_names') or []
        session_names = report_data.get('session_names') or []
        if pos_names:
            row += 1
            worksheet.merge_range(
                row, 0, row, last_col,
                _('Punto(s) de Venta: %s') % ', '.join(pos_names),
                subtitle_format,
            )
        if session_names:
            row += 1
            worksheet.merge_range(
                row, 0, row, last_col,
                _('Sesión(es): %s') % ', '.join(session_names),
                subtitle_format,
            )

        row += 2
        table_header_row = row
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_format)
        row += 1

        if is_totals:
            for line in report_data.get('total_lines', []):
                product_name = '%s%s' % (
                    line.get('code') and '[%s] ' % line['code'] or '',
                    line.get('product_name') or '',
                )
                worksheet.write(row, 0, product_name, text_format)
                worksheet.write_number(row, 1, line.get('quantity') or 0.0, qty_format)
                worksheet.write(row, 2, line.get('uom') or '', text_format)
                worksheet.write_number(row, 3, line.get('price_total') or 0.0, money_format)
                row += 1
        elif is_total_detailed:
            # ESI corrección: agrupar por Producto + UDM, sin fecha ni método de pago.
            # Ejemplo: PACEÑA NORMAL 2 CAJA y, debajo, PACEÑA NORMAL 3 Unidades.
            for line in report_data.get('total_detailed_lines', []):
                product_name = '%s%s' % (
                    line.get('code') and '[%s] ' % line['code'] or '',
                    line.get('product_name') or '',
                )
                worksheet.write(row, 0, product_name, text_format)
                worksheet.write_number(row, 1, line.get('quantity') or 0.0, qty_format)
                worksheet.write(row, 2, line.get('uom') or '', text_format)
                worksheet.write_number(row, 3, line.get('price_unit') or 0.0, money_format)
                worksheet.write_number(row, 4, line.get('price_total') or 0.0, money_format)
                row += 1
        else:
            for line in report_data.get('detailed_lines', []):
                product_name = '%s%s' % (
                    line.get('code') and '[%s] ' % line['code'] or '',
                    line.get('product_name') or '',
                )
                worksheet.write(row, 0, product_name, text_format)
                worksheet.write(row, 1, line.get('payment_method') or '', text_format)
                line_date = line.get('date')
                if line_date:
                    local_date = fields.Datetime.context_timestamp(self, line_date)
                    worksheet.write_datetime(row, 2, local_date.replace(tzinfo=None), date_format)
                else:
                    worksheet.write(row, 2, '', text_format)
                worksheet.write_number(row, 3, line.get('quantity') or 0.0, qty_format)
                worksheet.write(row, 4, line.get('uom') or '', text_format)
                worksheet.write_number(row, 5, line.get('price_unit') or 0.0, money_format)
                worksheet.write_number(row, 6, line.get('subtotal') or 0.0, money_format)
                row += 1

        if is_totals:
            data_lines = report_data.get('total_lines', [])
        elif is_total_detailed:
            data_lines = report_data.get('total_detailed_lines', [])
        else:
            data_lines = report_data.get('detailed_lines', [])
        if data_lines:
            worksheet.autofilter(table_header_row, 0, row - 1, last_col)
        worksheet.freeze_panes(table_header_row + 1, 0)

        # ESI corrección: en Detalles de ventas solo dejamos el control de ventas.
        row += 1
        label_end_col = max(last_col - 1, 0)
        if label_end_col > 0:
            worksheet.merge_range(row, 0, row, label_end_col, _('Total ventas:'), total_label_format)
        else:
            worksheet.write(row, 0, _('Total ventas:'), total_label_format)
        worksheet.write_number(
            row, last_col, report_data.get('detailed_total') or 0.0, total_money_format
        )

        # ------------------------------------------------------------------
        # HOJA 2: RESUMEN / CONTROL
        # ------------------------------------------------------------------
        summary = workbook.add_worksheet(_('Resumen')[:31])
        section_format = workbook.add_format({'bold': True, 'font_size': 12})
        label_format = workbook.add_format({'bold': True, 'border': 1})
        value_format = workbook.add_format({'border': 1})
        summary_money = workbook.add_format({
            'border': 1, 'num_format': '#,##0.00', 'align': 'right'
        })
        summary_money_bold = workbook.add_format({
            'bold': True, 'border': 1, 'num_format': '#,##0.00', 'align': 'right'
        })
        summary.set_column('A:A', 30)
        summary.set_column('B:B', 42)
        summary.set_column('C:C', 18)
        summary.merge_range('A1:C1', _('Resumen del reporte POS'), title_format)

        srow = 2
        for label, value in [
            (_('Empresa'), report_data.get('company_name') or ''),
            (_('Tipo de reporte'), report_data.get('report_type_label') or ''),
            (_('Desde'), fields.Datetime.to_string(date_start) if date_start else ''),
            (_('Hasta'), fields.Datetime.to_string(date_stop) if date_stop else ''),
            (_('Punto(s) de Venta'), ', '.join(pos_names)),
            (_('Sesión(es)'), ', '.join(session_names)),
        ]:
            summary.write(srow, 0, label, label_format)
            summary.merge_range(srow, 1, srow, 2, value, value_format)
            srow += 1

        srow += 1
        summary.write(srow, 0, _('Pagos'), section_format)
        srow += 1
        summary.write(srow, 0, _('Método de pago'), header_format)
        summary.write(srow, 1, _('Total'), header_format)
        srow += 1
        for payment in report_data.get('payments', []):
            summary.write(srow, 0, payment.get('name') or '', value_format)
            summary.write_number(srow, 1, payment.get('total') or 0.0, summary_money)
            srow += 1

        srow += 1
        summary.write(srow, 0, _('Impuestos'), section_format)
        srow += 1
        summary.write(srow, 0, _('Nombre'), header_format)
        summary.write(srow, 1, _('Importe impuesto'), header_format)
        summary.write(srow, 2, _('Importe base'), header_format)
        srow += 1
        for tax in report_data.get('taxes', []):
            summary.write(srow, 0, tax.get('name') or '', value_format)
            summary.write_number(srow, 1, tax.get('tax_amount') or 0.0, summary_money)
            summary.write_number(srow, 2, tax.get('base_amount') or 0.0, summary_money)
            srow += 1

        srow += 2
        for label, value, fmt in [
            (_('Total oficial Odoo'), report_data.get('total_paid') or 0.0, summary_money_bold),
            (_('Total ventas de líneas'), report_data.get('detailed_total') or 0.0, summary_money),
            (_('Diferencia de control'), report_data.get('total_difference') or 0.0, summary_money_bold),
        ]:
            summary.write(srow, 0, label, label_format)
            summary.write_number(srow, 2, value, fmt)
            srow += 1

        workbook.close()
        output.seek(0)

        if is_totals:
            mode = 'Totales'
        elif is_total_detailed:
            mode = 'Total_Detallado'
        else:
            mode = 'Detallado'
        filename = 'Detalles_de_ventas_POS_%s_%s.xlsx' % (
            mode,
            fields.Date.context_today(self).strftime('%Y%m%d'),
        )
        self.write({
            'excel_file': base64.b64encode(output.read()),
            'excel_filename': filename,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': (
                '/web/content?model=pos.details.wizard&id=%s&field=excel_file'
                '&filename_field=excel_filename&download=true'
            ) % self.id,
            'target': 'self',
        }
