from dateutil import parser
from datetime import datetime
from odoo import fields, models, api, _
from odoo import models
import logging
import json

_logger = logging.getLogger(__name__)


class RpPaymentSaleBleichnerXlsx(models.AbstractModel):
    _name = "report.report_xlsx.rp_payment_sale_bleichner_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Payment Sale Bleichner XLSX Report"

    def _get_report_name(self, report, data=False):
        company_id = data.get("company_id", False)
        report_name = _("Payment Sale Bleichner")
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
        day = data['day']
        user_id = data['user_id']
        partner_id = data['partner_id']
        branch_id = data['branch_id']
        sale_zone_id = data['sale_zone_id']
        company_id = data['company_id']
        report_title = "Reporte de Cobranzas"

        sheet = workbook.add_worksheet('Detalle de Cobranzas')
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
        letter3 = workbook.add_format({'font_size': 10, 'align': 'right', 'text_wrap': True})
        letter4 = workbook.add_format({'font_size': 10, 'align': 'left', 'text_wrap': True, 'bold': True})
        letter5 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': False, 'text_wrap': True, 'right': True, 'left': True,
                                       'bottom': True, 'top': True})
        letter_locked = letter3
        letter_locked.set_locked(False)

        sheet.set_column('A:A', 15, letter1)
        sheet.set_column('B:B', 15, letter1)
        sheet.set_column('C:C', 35, letter1)
        sheet.set_column('D:D', 30, letter1)
        sheet.set_column('E:E', 30, letter1)
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

        sheet.write(4, 0, 'FECHA', titulo2)
        sheet.write(4, 1, 'CODIGO CLIENTE', titulo2)
        sheet.write(4, 2, 'CLIENTE', titulo2)
        sheet.write(4, 3, 'DIARIO', titulo2)
        sheet.write(4, 4, 'GLOSA', titulo2)
        sheet.write(4, 5, 'TIPO DE PAGO', titulo2)
        sheet.write(4, 6, 'FACTURA PAGADA', titulo2)
        sheet.write(4, 7, 'COBRADA POR', titulo2)
        sheet.write(4, 8, 'DIA', titulo2)
        sheet.write(4, 9, 'ZONA', titulo2)
        sheet.write(4, 10, 'IMPORTE', titulo2)
        #sheet.write(4, 10, 'DIAS DE RETRASO', titulo2)
        sheet.freeze_panes(5, 0)

        filas = 4
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        arg_list = (start_date_obj, end_date_obj)
        filters = ""
        if partner_id:
            filters += ' AND l.partner_id={}'.format(partner_id)
        query = '''
            SELECT r.id ,r.debit_move_id, r.credit_move_id, r.max_date,mv.state_factura,mv.payment_reference,mv.amount_total
            FROM account_partial_reconcile r inner join account_move_line l on r.credit_move_id=l.id
            inner join account_move mv on mv.id=l.move_id
            where r.amount >0.1 AND l.date BETWEEN %s and %s 
            and mv.state_factura not in ('A','N')  and mv.move_type in ('entry','out_invoice','out_receipt') 
             and not l.partner_id is null
             ''' + filters + '''
             Order by l.date asc;
            '''

        print(query)
        cr.execute(query, arg_list)
        partial_reconciles = cr.dictfetchall()
        partial_reconcile_ids = [reconcile['id'] for reconcile in partial_reconciles if reconcile['id']]
        data = []
        for reconcile_id in partial_reconcile_ids:
            obj_reconcile = self.env["account.partial.reconcile"].search([('id', '=', reconcile_id)], limit=1)
            if day:
                if day != obj_reconcile.debit_move_id.move_id.day:
                    continue
            if user_id:
                if user_id != obj_reconcile.debit_move_id.move_id.user_id.id:
                    continue
            if branch_id:
                if branch_id != obj_reconcile.debit_move_id.move_id.branch_id.id:
                    continue
            if sale_zone_id:
                if sale_zone_id != obj_reconcile.debit_move_id.move_id.sale_zone_id.id:
                    continue
            rp_payment_sale_id = self.env['rp.payment.sale.route.line'].create({
                'account_partial_reconcile_id': obj_reconcile.id,
                'move_line_id_debit': obj_reconcile.debit_move_id.id,
                'move_id_debit': obj_reconcile.debit_move_id.move_id.id,
                'move_line_id_credit': obj_reconcile.credit_move_id.id,
                'move_id_credit': obj_reconcile.credit_move_id.move_id.id,
            })
            data.append(rp_payment_sale_id.id)
            print(str(reconcile_id))
        rp_payment_sale_id = self.env['rp.payment.sale.route'].create({
            'payment_sale_lines': [(6, False, data)],
            'company_id': company_id,
            'start_date': start_date,
            'end_date': end_date
        })

        amount_total = 0
        for rec in rp_payment_sale_id.payment_sale_lines:
            filas += 1
            sheet.write(filas, 0, rec.move_line_id_credit.date.strftime('%d/%m/%Y'), letter5)
            sheet.write(filas, 1, rec.move_line_id_credit.partner_id.partner_code or '', letter5)
            sheet.write(filas, 2, rec.move_line_id_credit.partner_id.name or '', letter5)

            sheet.write(filas, 3, rec.move_id_credit.journal_id.name or '', letter5)
            sheet.write(filas, 4, rec.move_id_debit.narration or '', letter5)
            sheet.write(filas, 5, rec.move_line_id_credit.name or '', letter5)
            sheet.write(filas, 6, rec.move_id_debit.nro_factura or '', letter5)
            sheet.write(filas, 7, rec.move_id_debit.user_id.name or '', letter5)
            sheet.write(filas, 8, rec.move_id_debit.day or '', letter5)
            sheet.write(filas, 9, rec.move_id_debit.sale_zone_id.name or '', letter5)
            amount = rec.account_partial_reconcile_id.amount
            amount_total += amount
            sheet.write(filas, 10, amount, number_right)

        if amount_total > 0:
            filas += 1
            sheet.write(filas, 10, amount_total, number_right_bold)
            sheet.merge_range('A{0}:I{0}'.format(str(filas + 1)), 'Total', titulo1)
