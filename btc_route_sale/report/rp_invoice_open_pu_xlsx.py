from dateutil import parser
from datetime import datetime
from odoo import fields, models, api, _
from odoo import models
import logging
import json

_logger = logging.getLogger(__name__)


class RpPaymentPurchaseXlsx(models.AbstractModel):
    _name = "report.report_xlsx.rp_invoice_open_pu_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Open invoice Purchase XLSX Report"

    def _get_report_name(self, report, data=False):
        company_id = data.get("company_id", False)
        report_name = _("Payment Purchase")
        if company_id:
            company = self.env["res.company"].browse(company_id)
            suffix = " - {} - {}".format(company.name, company.currency_id.name)
            report_name = report_name + suffix
        return report_name

    def generate_xlsx_report(self, workbook, data, lines):
        obj = self.env['rp.payment.sale.route']
        cr = self.env.cr
        start_date = data['start_date']
        end_date = data['end_date']
        domain = data['domain']
        domain_line = data['domain']
        day = data['day']
        user_id = data['user_id']
        partner_id = data['partner_id']
        branch_id = data['branch_id']
        sale_zone_id = data['sale_zone_id']
        company_id = data['company_id']
        report_title = "Reporte de Cuentas por Pagar"

        sheet = workbook.add_worksheet('Detalle de Cuentas por Pagar')
        titulo1 = workbook.add_format({'font_size': 16, 'align': 'center', 'text_wrap': True, 'bold': True})
        titulo2 = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'text_wrap': True, 'bottom': True, 'top': True, 'bold': True})
        titulo3 = workbook.add_format(
            {'font_size': 12, 'align': 'left', 'text_wrap': True, 'bottom': True, 'top': True, 'bold': True})
        titulo3_number = workbook.add_format(
            {'font_size': 12, 'align': 'right', 'text_wrap': True, 'bottom': True, 'top': True, 'bold': True,
             'num_format': '#,##0.00'})
        titulo4 = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'text_wrap': True, 'bottom': True, 'top': True, 'left': True,
             'right': True, 'bold': True})

        number_left = workbook.add_format({'font_size': 10, 'align': 'left', 'num_format': '#,##0.00'})
        number_right_integer = workbook.add_format({'font_size': 10, 'align': 'right', 'num_format': '#0', 'right': True, 'left': True,
                                       'bottom': True, 'top': True})
        number_right = workbook.add_format({'font_size': 10, 'align': 'right', 'num_format': '#,##0.00', 'right': True, 'left': True,
                                       'bottom': True, 'top': True})
        number_right_bold = workbook.add_format(
            {'font_size': 10, 'align': 'right', 'num_format': '#,##0.00', 'bold': True, 'right': True, 'left': True,
                                       'bottom': True, 'top': True})
        number_right_col = workbook.add_format(
            {'font_size': 10, 'align': 'right', 'num_format': '#,##0.00', 'bg_color': 'silver'})
        number_center = workbook.add_format({'font_size': 10, 'align': 'center', 'num_format': '#,##0.00'})
        number_right_col.set_locked(False)

        letter1 = workbook.add_format({'font_size': 10, 'align': 'left', 'text_wrap': True})
        letter2 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
        letter3 = workbook.add_format({'font_size': 10, 'align': 'right', 'text_wrap': True, 'right': True, 'left': True,
                                       'bottom': True, 'top': True})
        letter4 = workbook.add_format({'font_size': 10, 'align': 'left', 'text_wrap': True, 'bold': True})
        letter5 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': False, 'text_wrap': True, 'right': True, 'left': True,
                                       'bottom': True, 'top': True})
        letter_locked = letter3
        letter_locked.set_locked(False)

        sheet.set_column('A:A', 15, letter1)
        sheet.set_column('B:B', 15, letter1)
        sheet.set_column('C:C', 35, letter1)
        sheet.set_column('D:D', 30, letter1)
        sheet.set_column('E:E', 15, letter1)
        sheet.set_column('F:F', 15, letter1)
        sheet.set_column('G:G', 20, letter1)
        sheet.set_column('H:H', 15, letter1)
        sheet.set_column('I:I', 15, letter1)
        sheet.set_column('J:J', 15, letter1)
        sheet.set_column('K:K', 20, letter1)

        sheet.merge_range('A1:J1', report_title, titulo1)

        fecha_inicial = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        fecha_final = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        sheet.write(1, 0, 'Rango de Fechas: ', letter4)
        sheet.merge_range('B2:D2', fecha_inicial + ' - ' + fecha_final)
        sheet.write(2, 0, 'BLEICHNER: ', letter4)
        filter_location_name = 'Casa Matriz'
 
        sheet.merge_range('B3:D3', filter_location_name)

        sheet.write(4, 0, 'FECHA RECEPCIÓN', titulo2)
        sheet.write(4, 1, 'CODIGO CLIENTE', titulo2)
        sheet.write(4, 2, 'CLIENTE', titulo2)
        sheet.write(4, 3, 'VENDEDOR', titulo2)
        sheet.write(4, 4, 'DIA', titulo2)
        sheet.write(4, 5, 'ZONA', titulo2)
        sheet.write(4, 6, 'NRO FACTURA', titulo2)
        sheet.write(4, 7, 'TOTAL COMPRAS', titulo2)
        sheet.write(4, 8, 'PAGOS', titulo2)
        sheet.write(4, 9, 'IMPAGA', titulo2)
        sheet.write(4, 10, 'DIAS', titulo2)
        #sheet.write(4, 10, 'DIAS DE RETRASO', titulo2)
        sheet.freeze_panes(5, 0)

        filas = 4

        domain = [('company_id', '=', company_id)]
        domain += [('state', '=', 'posted')]
        domain += [('state', '!=', 'draft')]
        #domain += [('state_factura', '=', 'V')]
        #domain += [('move_type', '=', 'out_invoice')]
        domain += [('move_type', 'in', ('in_invoice', 'in_receipt'))]
        domain += [('payment_state', '!=', 'paid')]
        domain += [('payment_state', '!=', 'reversed')]

        domain_line = [('company_id', '=', company_id)]
        domain_line += [('move_id.is_account_payable', '=', True)]
        domain_line += [('credit', '>', 0.0)]
        if branch_id:
            domain += [('branch_id.id', '=', branch_id)]
            domain_line += [('move_id.branch_id.id', '=', branch_id)]
        if user_id:
            domain += [('user_id.id', '=', user_id)]
            domain_line += [('move_id.user_id.id', '=', branch_id)]
        if day:
            domain += [('day', '=', day)]
        if partner_id:
            domain += [('partner_id.id', '=', partner_id)]
            domain_line += [('partner_id.id', '=', partner_id)]
        if sale_zone_id:
            domain += [('sale_zone_id.id', '=', sale_zone_id)]

        obj_account_due = self.env['account.move.line'].search(domain_line)
        #[('move_id.is_account_receivable', '=', True),
        #                                                    ('debit', '>', 0.0)])
        obj_invoices = self.env['account.move'].search(domain).sorted(key=lambda r: r.partner_id).ids
        rp_invoice_sale_id = self.env['rp.open.invoice.report'].create({
            'invoice_ids': [(6, False, obj_invoices)],
            'company_id': company_id,
            'start_date': start_date,
            'end_date': end_date
        })

        amount_total = 0
        amount_pay = 0
        amount_due = 0
        for rec in rp_invoice_sale_id.invoice_ids:
            filas += 1
            sheet.write(filas, 0, rec.date.strftime('%d/%m/%Y'), letter5)
            sheet.write(filas, 1, rec.partner_id.partner_code or '', letter5)
            sheet.write(filas, 2, rec.partner_id.name or '', letter5)

            sheet.write(filas, 3, rec.user_id.name or '', letter5)
            sheet.write(filas, 4, rec.day or '', letter5)
            sheet.write(filas, 5, rec.sale_zone_id.name or '', letter5)
            sheet.write(filas, 6, rec.nro_factura or '', letter5)
            sheet.write(filas, 7, rec.amount_total, number_right)
            sheet.write(filas, 8, rec.amount_paid_tmp, number_right)
            sheet.write(filas, 9, rec.amount_residual, number_right)

            amount_total += rec.amount_total
            amount_pay += rec.amount_paid_tmp
            amount_due += rec.amount_residual
            diff_days = rp_invoice_sale_id.get_days_difference(date_begin=rec.invoice_date_due)
            sheet.write(filas, 10, diff_days, letter3)

        for rec in obj_account_due:
            partial_reconcile_ids = self.env['account.partial.reconcile'].search([('debit_move_id', '=', rec.id)])
            total_paid = sum(rec.debit for rec in partial_reconcile_ids.debit_move_id)
            total_due = rec.credit - total_paid
            if total_due > 0.01:
                amount_total += rec.credit
                amount_pay += total_paid
                amount_due += total_due
                filas += 1
                sheet.write(filas, 0, rec.move_id.date.strftime('%d/%m/%Y'), letter5)
                sheet.write(filas, 1, rec.partner_id.partner_code or '', letter5)
                sheet.write(filas, 2, rec.partner_id.name or '', letter5)

                sheet.write(filas, 3, rec.move_id.user_id.name or '', letter5)
                sheet.write(filas, 4, rec.move_id.day or '', letter5)
                sheet.write(filas, 5, rec.move_id.sale_zone_id.name or '', letter5)
                sheet.write(filas, 6, rec.move_id.nro_factura or '', letter5)
                sheet.write(filas, 7, rec.credit, number_right)

                sheet.write(filas, 8, total_paid, number_right)
                sheet.write(filas, 9, total_due, number_right)

                diff_days = rp_invoice_sale_id.get_days_difference(date_begin=rec.move_id.invoice_date_due)
                sheet.write(filas, 10, diff_days, letter3)

        if amount_total > 0:
            filas += 1
            sheet.write(filas, 7, amount_total, number_right_bold)
            sheet.write(filas, 8, amount_pay, number_right_bold)
            sheet.write(filas, 9, amount_due, number_right_bold)
            sheet.merge_range('A{0}:G{0}'.format(str(filas + 1)), 'Total', titulo1)
