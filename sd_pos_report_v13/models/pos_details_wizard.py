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

    # ESI corrección: archivo temporal para descargar Excel directamente desde Odoo.
    # No requiere report_xlsx ni módulos externos de Odoo.
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
        }

    def action_view_report(self):
        """Open an HTML preview instead of forcing an immediate PDF download."""
        self.ensure_one()
        # ESI corrección: la vista previa conserva el ID del wizard para que el
        # botón Excel del visor HTML pueda generar exactamente el mismo reporte.
        preview_data = self._sd_prepare_report_data()
        preview_data.update({
            'sd_pos_report_excel': True,
            'sd_pos_report_wizard_id': self.id,
        })
        # ESI corrección: vista previa QWeb HTML similar a los reportes navegables de Odoo.
        return self.env.ref(
            'sd_pos_report_v13.sale_details_report_html'
        ).report_action([], data=preview_data)

    def generate_report(self):
        """Print the report as PDF using the exact same filters as the preview."""
        self.ensure_one()
        # ESI corrección: PDF y vista previa comparten exactamente la misma información.
        return self.env.ref('point_of_sale.sale_details_report').report_action(
            [], data=self._sd_prepare_report_data()
        )

    def action_export_xlsx(self):
        """Generate and download an XLSX with detail + audit summary."""
        self.ensure_one()

        # ESI corrección: Excel usa exactamente la misma lógica central que HTML/PDF,
        # evitando que el total o los filtros cambien entre formatos.
        report_data = self.env[
            'report.point_of_sale.report_saledetails'
        ]._get_report_values([], data=self._sd_prepare_report_data())

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            # ESI corrección: Odoo maneja fechas con zona horaria; Excel recibe fecha sin tz.
            'remove_timezone': True,
        })

        # ---------------------------------------------------------------------
        # HOJA 1: DETALLE DE VENTAS
        # ---------------------------------------------------------------------
        worksheet = workbook.add_worksheet(_('Detalle de ventas')[:31])

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
        })
        subtitle_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
        })
        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })
        text_format = workbook.add_format({'border': 1, 'valign': 'top'})
        qty_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00',
            'align': 'right',
        })
        money_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00',
            'align': 'right',
        })
        date_format = workbook.add_format({
            'border': 1,
            'num_format': 'dd/mm/yyyy hh:mm:ss',
            'align': 'center',
        })
        total_label_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'right',
        })
        total_money_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '#,##0.00',
            'align': 'right',
        })

        worksheet.set_column('A:A', 38)
        worksheet.set_column('B:B', 24)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:F', 16)

        worksheet.merge_range('A1:F1', _('Detalles de ventas POS'), title_format)
        worksheet.merge_range(
            'A2:F2',
            report_data.get('company_name') or self.env.company.name,
            subtitle_format,
        )

        date_start = report_data.get('date_start')
        date_stop = report_data.get('date_stop')
        period_text = '%s - %s' % (
            fields.Datetime.to_string(date_start) if date_start else '',
            fields.Datetime.to_string(date_stop) if date_stop else '',
        )
        worksheet.merge_range('A3:F3', period_text, subtitle_format)

        pos_names = report_data.get('config_names') or []
        session_names = report_data.get('session_names') or []
        header_row = 3
        if pos_names:
            header_row += 1
            worksheet.merge_range(
                header_row - 1, 0, header_row - 1, 5,
                _('Punto(s) de Venta: %s') % ', '.join(pos_names),
                subtitle_format,
            )
        if session_names:
            header_row += 1
            worksheet.merge_range(
                header_row - 1, 0, header_row - 1, 5,
                _('Sesión(es): %s') % ', '.join(session_names),
                subtitle_format,
            )

        row = header_row + 1
        headers = [
            _('Producto'),
            _('Método de pago'),
            _('Fecha'),
            _('Cantidad'),
            _('Precio Unitario'),
            _('Subtotal'),
        ]
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_format)
        table_header_row = row
        row += 1
        first_data_row = row

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
                worksheet.write_datetime(
                    row, 2, local_date.replace(tzinfo=None), date_format
                )
            else:
                worksheet.write(row, 2, '', text_format)

            worksheet.write_number(row, 3, line.get('quantity') or 0.0, qty_format)
            worksheet.write_number(row, 4, line.get('price_unit') or 0.0, money_format)
            worksheet.write_number(row, 5, line.get('subtotal') or 0.0, money_format)
            row += 1

        last_data_row = max(row - 1, first_data_row)
        if report_data.get('detailed_lines'):
            worksheet.autofilter(table_header_row, 0, last_data_row, 5)
        worksheet.freeze_panes(table_header_row + 1, 0)

        # ESI corrección: el total mostrado es el TOTAL OFICIAL DE ODOO (amount_total
        # de los pedidos), no una fórmula nueva inventada por el Excel.
        row += 1
        worksheet.merge_range(row, 0, row, 4, _('Total Odoo:'), total_label_format)
        worksheet.write_number(
            row, 5, report_data.get('total_paid') or 0.0, total_money_format
        )

        # ---------------------------------------------------------------------
        # HOJA 2: RESUMEN / CONTROL DE TOTALES
        # ---------------------------------------------------------------------
        summary = workbook.add_worksheet(_('Resumen')[:31])
        section_format = workbook.add_format({'bold': True, 'font_size': 12})
        label_format = workbook.add_format({'bold': True, 'border': 1})
        value_format = workbook.add_format({'border': 1})
        summary_money = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00',
            'align': 'right',
        })
        summary_money_bold = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '#,##0.00',
            'align': 'right',
        })

        summary.set_column('A:A', 28)
        summary.set_column('B:B', 42)
        summary.set_column('C:C', 18)
        summary.merge_range('A1:C1', _('Resumen del reporte POS'), title_format)

        srow = 2
        summary.write(srow, 0, _('Empresa'), label_format)
        summary.merge_range(srow, 1, srow, 2, report_data.get('company_name') or '', value_format)
        srow += 1
        summary.write(srow, 0, _('Desde'), label_format)
        summary.merge_range(srow, 1, srow, 2, fields.Datetime.to_string(date_start) if date_start else '', value_format)
        srow += 1
        summary.write(srow, 0, _('Hasta'), label_format)
        summary.merge_range(srow, 1, srow, 2, fields.Datetime.to_string(date_stop) if date_stop else '', value_format)
        srow += 1
        summary.write(srow, 0, _('Punto(s) de Venta'), label_format)
        summary.merge_range(srow, 1, srow, 2, ', '.join(pos_names), value_format)
        srow += 1
        summary.write(srow, 0, _('Sesión(es)'), label_format)
        summary.merge_range(srow, 1, srow, 2, ', '.join(session_names), value_format)

        srow += 2
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
        summary.write(srow, 0, _('Total oficial Odoo'), label_format)
        summary.write_number(srow, 2, report_data.get('total_paid') or 0.0, summary_money_bold)
        srow += 1
        summary.write(srow, 0, _('Suma de subtotales de líneas'), label_format)
        summary.write_number(srow, 2, report_data.get('detailed_total') or 0.0, summary_money)
        srow += 1
        summary.write(srow, 0, _('Diferencia de control'), label_format)
        summary.write_number(srow, 2, report_data.get('total_difference') or 0.0, summary_money_bold)

        workbook.close()
        output.seek(0)

        # ESI corrección: nombre descriptivo para identificar rápidamente el archivo.
        filename = 'Detalles_de_ventas_POS_%s.xlsx' % fields.Date.context_today(self).strftime('%Y%m%d')
        self.write({
            'excel_file': base64.b64encode(output.read()),
            'excel_filename': filename,
        })

        # ESI corrección: descarga directa del XLSX desde el wizard.
        return {
            'type': 'ir.actions.act_url',
            'url': (
                '/web/content?model=pos.details.wizard&id=%s&field=excel_file'
                '&filename_field=excel_filename&download=true'
            ) % self.id,
            'target': 'self',
        }
