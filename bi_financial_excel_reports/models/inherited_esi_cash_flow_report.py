# -*- coding: utf-8 -*-
import base64
import io
import xlwt
from odoo import models


class EsiCashFlowReportWizardExcel(models.TransientModel):
    _inherit = 'esi.cash.flow.report.wizard'

    def action_print_excel(self):
        self.ensure_one()
        data = self._prepare_report_data()
        workbook = xlwt.Workbook(style_compression=2)
        ws = workbook.add_sheet('Flujo de Caja', cell_overwrite_ok=True)
        title = xlwt.easyxf('font: bold on, height 300; align: horiz center')
        head = xlwt.easyxf('font: bold on; align: horiz center; borders: bottom thin')
        money = xlwt.easyxf('align: horiz right', num_format_str='#,##0.00')
        bold_money = xlwt.easyxf('font: bold on; align: horiz right', num_format_str='#,##0.00')
        ws.write_merge(0, 0, 0, 8, 'REPORTE DE FLUJO DE CAJA', title)
        ws.write(1, 0, 'Empresa'); ws.write(1, 1, self.company_id.name or '')
        ws.write(2, 0, 'Desde'); ws.write(2, 1, str(self.date_from or ''))
        ws.write(2, 2, 'Hasta'); ws.write(2, 3, str(self.date_to or ''))
        filters=[]
        if self.cash_flow_ids: filters.append('Cuentas de flujo: %s' % ', '.join(self.cash_flow_ids.mapped('display_name')))
        if self.flow_type: filters.append('Tipo: %s' % dict(self._fields['flow_type'].selection).get(self.flow_type, self.flow_type))
        if self.analytic_account_ids: filters.append('Analítica: %s' % ', '.join(self.analytic_account_ids.mapped('display_name')))
        if self.partner_ids: filters.append('Empresa: %s' % ', '.join(self.partner_ids.mapped('display_name')))
        if filters: ws.write_merge(3, 3, 0, 8, ' | '.join(filters))
        headers=['Fecha','Comprobante','CTA Flujo','Analítica','Empresa','Banco / Caja','Ingreso','Egreso','Neto']
        for c,h in enumerate(headers): ws.write(5,c,h,head)
        widths=[3000,5200,6200,6200,7200,7000,4200,4200,4200]
        for c,w in enumerate(widths): ws.col(c).width=w
        row=6
        for r in data['rows']:
            vals=[str(r.get('date') or ''),r.get('move_name') or '',r.get('flow') or '',r.get('analytic') or '',r.get('partner') or '',r.get('account') or '']
            for c,v in enumerate(vals): ws.write(row,c,v)
            ws.write(row,6,r.get('income',0.0),money); ws.write(row,7,r.get('expense',0.0),money); ws.write(row,8,r.get('net',0.0),money)
            row+=1
        ws.write_merge(row,row,0,5,'TOTAL',head)
        ws.write(row,6,data['total_income'],bold_money); ws.write(row,7,data['total_expense'],bold_money); ws.write(row,8,data['total_net'],bold_money)
        fp=io.BytesIO(); workbook.save(fp)
        filename='Flujo_de_Caja_%s_%s.xls' % (self.date_from,self.date_to)
        export=self.env['excel.report'].create({'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
        return {'view_mode':'form','res_id':export.id,'res_model':'excel.report','view_type':'form','type':'ir.actions.act_window','target':'new'}
