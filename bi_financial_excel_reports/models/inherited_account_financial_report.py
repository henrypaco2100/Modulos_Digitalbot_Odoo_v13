# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import xlwt
import base64
import io
from odoo.exceptions import UserError

class AccountingReportBi(models.TransientModel):
	_inherit = "accounting.report.bi"
	# excel_file = fields.Binary('Reporte Excel')
	# file_name = fields.Char('Archivo Excel', size=64)


	def _print_excel(self,report_lines,report_name):
		if report_name == 'balance_sheet':
			return self._print_balance_sheet_excel_report(report_lines)
		elif report_name == 'general_ledger':
			return self._print_general_ledger_excel_report(report_lines)
		elif report_name == 'trial_balance':
			return self._print_trial_balance_excel_report(report_lines)
		else:
			raise UserError('Mala configuración. Actualice el módulo.\n No hay ningún informe asociado.')

	def _print_balance_sheet_excel_report(self,report_lines):
		filename = self.account_report_id.name
		filename += '.xls'
		workbook = xlwt.Workbook(style_compression=2)
		worksheet = workbook.add_sheet('Sheet 1', cell_overwrite_ok=True)
		date_format = xlwt.XFStyle()
		date_format.num_format_str = 'dd/mm/yyyy'
		style_header = xlwt.easyxf(
			"font:height 300; font: name Liberation Sans, bold on,color black; align: horiz center,vert center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour gray25")
		worksheet.row(0).height_mismatch = True
		worksheet.row(0).height = 500
		worksheet.col(1).width = 13000
		worksheet.col(2).width = 5500
		worksheet.col(3).width = 5500
		worksheet.col(4).width = 5500
		# worksheet.row(6).height = 300
		# worksheet.row(15).height = 300
		# worksheet.row(16).height = 300
		# worksheet.row(18).height = 300
		width_title = 4
		if self.debit_credit:
			width_title = 5


		worksheet.write_merge(0, 0, 0, width_title-1, self.account_report_id.name + " INFORME", style=style_header)

		style_cell = xlwt.easyxf("font: bold on,color black; align: horiz left; borders: left thin, right thin, top thin")
		style_cell2 = xlwt.easyxf("font: color black; align: horiz left; borders: left thin, right thin, bottom thin")
		for col in range(width_title):
			worksheet.write(1, col, style=style_cell)
			worksheet.write(2, col, style=style_cell2)
		worksheet.write(1, 1, 'Movimiento objetivo:', style=style_cell)
		if self.date_from:
			worksheet.write(1,2,'Fecha de inicio:', style=style_cell)
		if self.date_to:
			worksheet.write(1,3,'Fecha final:', style=style_cell)
		worksheet.write(2,1,'Todas las entradas publicadas' if self.target_move == 'posted' else 'Todas las entradas', style=style_cell2)
		if self.date_from:
			worksheet.write(2,2,str(self.date_from), style=style_cell2)
		if self.date_to:
			worksheet.write(2,3,str(self.date_to), style=style_cell2)
		if self.debit_credit:
			style_cell = xlwt.easyxf("font: bold on,color black; align: horiz center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour gray25")
			worksheet.write(3, 0, 'Cuenta', style=style_cell)
			worksheet.write(3, 1, 'Nombre', style=style_cell)
			worksheet.write(3, 2, 'Debito', style=style_cell)
			worksheet.write(3, 3, 'Credito', style=style_cell)
			worksheet.write(3, 4, 'Balance', style=style_cell)
			row = 4
			col = 0
			for lines in report_lines:
				account_number = lines.get('number_cuenta')
				if lines.get('level') != 0:
					if lines.get('level') > 3:
						style_line = xlwt.easyxf("font:color black; borders: left thin, right thin, top thin, bottom thin")
						worksheet.write(row, col + 1, '     ' + lines.get('name'), style_line)
					else:
						style_line = xlwt.easyxf("font:bold on,color black; borders: left thin, right thin, top thin, bottom thin")
						worksheet.write(row, col + 1, lines.get('name').upper(), style_line)
					if account_number:
						worksheet.write(row, col, account_number, style_line)
					else:
						worksheet.write(row, col, '', xlwt.easyxf("borders: left thin, right thin, top thin, bottom thin"))
					# worksheet.write(row, col+1, lines.get('name'),style_line)
					worksheet.write(row, col+2, lines.get('debit'), style_line)
					worksheet.write(row, col+3, lines.get('credit'), style_line)
					worksheet.write(row, col+4, lines.get('balance'), style_line)
					row += 1
		elif not self.enable_filter and not self.debit_credit:
			# worksheet.write_merge(0, 0, 0, width_title, self.account_report_id.name + " INFORME", style=style_header)
			style_cell = xlwt.easyxf("font: bold on,color black; align: horiz center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour gray25")
			worksheet.write(3, 0, 'Cuenta', style=style_cell)
			worksheet.write(3, 1, 'Nombre', style=style_cell)
			worksheet.write_merge(3, 3, 2, 3, 'Balance', style=style_cell)

			row = 4
			col = 0
			for lines in report_lines:
				account_number = lines.get('number_cuenta')
				if lines.get('level') != 0:
					if lines.get('level') > 3:
						style_line = xlwt.easyxf(
							"font:color black; borders: left thin, right thin, top thin, bottom thin")
						worksheet.write(row, col + 1, '     ' + lines.get('name'), style_line)
					else:
						style_line = xlwt.easyxf(
							"font:bold on,color black; borders: left thin, right thin, top thin, bottom thin")
						worksheet.write(row, col + 1, lines.get('name').upper(), style_line)
					if account_number:
						worksheet.write(row, col, account_number, style_line)
					else:
						worksheet.write(row, col, '', xlwt.easyxf("borders: left thin, right thin, top thin, bottom thin"))

					worksheet.write_merge(row, row, col + 2, col + 3, lines.get('balance'), style_line)

					row += 1
		else:
			style_cell = xlwt.easyxf(
				"font: bold on,color black; align: horiz center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour gray25")
			worksheet.write(3, 0, 'Cuenta', style=style_cell)
			worksheet.write(3, 1, 'Nombre', style=style_cell)
			worksheet.write(3, 2, 'Balance', style=style_cell)
			worksheet.write(3, 3, self.label_filter, style=style_cell)

			row = 4
			col = 0
			for lines in report_lines:
				account_number = lines.get('number_cuenta')
				if lines.get('level') != 0:
					if lines.get('level') > 3:
						style_line = xlwt.easyxf(
							"font:color black; borders: left thin, right thin, top thin, bottom thin")
						worksheet.write(row, col + 1, '     ' + lines.get('name'), style_line)
					else:
						style_line = xlwt.easyxf(
							"font:bold on,color black; borders: left thin, right thin, top thin, bottom thin")
						worksheet.write(row, col + 1, lines.get('name').upper(), style_line)
					if account_number:
						worksheet.write(row, col, account_number, style_line)
					else:
						worksheet.write(row, col, '', xlwt.easyxf("borders: left thin, right thin, top thin, bottom thin"))

					worksheet.write(row, col + 2, lines.get('balance'), style_line)
					worksheet.write(row, col + 3, lines.get('balance_cmp'), style_line)
					row += 1
		fp = io.BytesIO()
		workbook.save(fp)

		export_id = self.env['excel.report'].create(
			{'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
		res = {
			'view_mode': 'form',
			'res_id': export_id.id,
			'res_model': 'excel.report',
			'view_type': 'form',
			'type': 'ir.actions.act_window',
			'target': 'new'
		}
		return res

	def check_report(self):
		res = super(AccountingReportBi, self).check_report()
		if self._context.get('report_type') == 'excel':
			report_lines = res.get('data').get('report_lines')
			return self._print_excel(report_lines, report_name='balance_sheet')
		else:
			return res
	def check_report_estado_resultado(self):
		res = super(AccountingReportBi, self).check_report_estado_resultado()
		if self._context.get('report_type') == 'excel':
			report_lines = res.get('data').get('report_lines')
			return self._print_excel(report_lines, report_name='balance_sheet')
		else:
			return res


def _print_general_ledger_excel_report(self, report_lines):
	filename = 'Libro mayor.xls'
	workbook = xlwt.Workbook(style_compression=2)
	worksheet = workbook.add_sheet('Sheet 1', cell_overwrite_ok=True)
	date_format = xlwt.XFStyle()
	date_format.num_format_str = 'dd/mm/yyyy'
	style_header = xlwt.easyxf(
		"font:height 300; font: name Liberation Sans, bold on,color black; align: horiz center; borders: top thin, bottom thin, right thin, left thin; pattern: pattern solid, fore_colour gray25")
	style_line = xlwt.easyxf(
		"font:bold on,color black; align: horiz center; border: right thin, left thin, bottom thin")
	worksheet.row(0).height_mismatch = True
	worksheet.row(0).height = 500
	worksheet.row(2).height = 550
	worksheet.col(1).width = 5500
	worksheet.col(2).width = 6500
	worksheet.col(3).width = 6500
	worksheet.col(4).width = 5500
	worksheet.col(5).width = 8000

	show_analytic = bool(self.esi_con_analitica)
	analytic_col = 6 if show_analytic else None
	debit_col = 7 if show_analytic else 6
	credit_col = debit_col + 1
	balance_col = debit_col + 2
	if show_analytic:
		worksheet.col(analytic_col).width = 6500

	worksheet.write_merge(0, 0, 0, balance_col,
		self.env['res.users'].browse(self.env.uid).company_id.name + " : Informe del libro mayor ",
		style=style_header)
	worksheet.write_merge(1, 1, 0, 1, 'Diarios', style_line)
	worksheet.write(1, 2, 'Mostrar cuenta', style_line)
	worksheet.write(1, 3, 'Movimientos de destino', style_line)
	worksheet.write(1, 4, 'Ordenado por', style_line)
	if self.date_from:
		worksheet.write(1, 5, 'Fecha de', style_line)
	if self.date_to:
		worksheet.write_merge(1, 1, 6, balance_col, 'Fecha hasta', style_line)

	style_line = xlwt.easyxf("font: height 150, color black; align: wrap yes; border: right thin, left thin, bottom thin")
	if self.journal_ids and len(self.journal_ids) > 0:
		journals_id = ', '.join([lt.code or '' for lt in self.journal_ids])
		worksheet.write_merge(2, 2, 0, 1, journals_id, style_line)
	else:
		journals_i = self.env['account.journal'].search([])
		journals_ids = ', '.join([lt.code or '' for lt in journals_i])
		worksheet.write_merge(2, 2, 0, 1, journals_ids, style_line)

	style_line = xlwt.easyxf("font: color black; align: horiz center, vert center; border: right thin, left thin, bottom thin")
	if self.display_account == 'all':
		display_account = 'Todas las cuentas'
	elif self.display_account == 'movement':
		display_account = 'Con movimientos'
	else:
		display_account = 'Con saldo no igual a cero'
	worksheet.write(2, 2, display_account, style_line)
	worksheet.write(2, 3, 'Todas las entradas publicadas' if self.target_move == 'posted' else 'Todas las entradas', style_line)
	worksheet.write(2, 4, 'Fecha' if self.sortby == 'sort_date' else 'Diario y Asociado', style_line)
	if self.date_from:
		worksheet.write(2, 5, str(self.date_from), style_line)
	if self.date_to:
		worksheet.write_merge(2, 2, 6, balance_col, str(self.date_to), style_line)

	style_head = xlwt.easyxf("font:color black; align: horiz center; border: right thin, left thin, bottom thin; pattern: pattern solid, fore_colour gray25")
	headers = ['Fecha', 'Diario', 'Asociado', 'Ref', 'Asiento', 'Etiqueta de entrada']
	for idx, title in enumerate(headers):
		worksheet.write(3, idx, title, style_head)
	if show_analytic:
		worksheet.write(3, analytic_col, 'Analítica', style_head)
	worksheet.write(3, debit_col, 'Débito', style_head)
	worksheet.write(3, credit_col, 'Crédito', style_head)
	worksheet.write(3, balance_col, 'Balance', style_head)

	row = 4
	for line in report_lines:
		account_style = xlwt.easyxf("font: bold on, color black; border: right thin, left thin, bottom thin, top thin")
		worksheet.write_merge(row, row, 0, debit_col - 1,
			(line.get('code') or '') + (line.get('name') or '').upper(), style=account_style)
		worksheet.write(row, debit_col, line.get('debit'), style=account_style)
		worksheet.write(row, credit_col, line.get('credit'), style=account_style)
		worksheet.write(row, balance_col, line.get('balance'), style=account_style)
		row += 1
		flag = False
		for move_line in line.get('move_lines') or []:
			line_style = xlwt.easyxf("font:color black; border: right thin, left thin, bottom thin, top thin")
			worksheet.write(row, 0, str(move_line.get('ldate') or ''), line_style)
			worksheet.write(row, 1, move_line.get('lcode') or '', line_style)
			worksheet.write(row, 2, move_line.get('partner_name') or '', line_style)
			worksheet.write(row, 3, move_line.get('lref') or '', line_style)
			worksheet.write(row, 4, move_line.get('move_name') or '', line_style)
			worksheet.write(row, 5, move_line.get('lname') or '', line_style)
			if show_analytic:
				worksheet.write(row, analytic_col, move_line.get('analytic_name') or '', line_style)
			worksheet.write(row, debit_col, move_line.get('debit'), line_style)
			worksheet.write(row, credit_col, move_line.get('credit'), line_style)
			worksheet.write(row, balance_col, move_line.get('balance'), line_style)
			flag = True
			row += 1
		if not flag:
			row += 1

	fp = io.BytesIO()
	workbook.save(fp)
	export_id = self.env['excel.report'].create(
		{'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
	return {
		'view_mode': 'form', 'res_id': export_id.id, 'res_model': 'excel.report',
		'view_type': 'form', 'type': 'ir.actions.act_window', 'target': 'new'
	}

	def print_general_ledger(self):
		res = super(AccountingReportBi, self).print_general_ledger()
		if self._context.get('report_type') == 'excel':
			report_lines = res.get('data').get('Account')
			return self._print_excel(report_lines,report_name='general_ledger')
		else:
			return res

	def _print_trial_balance_excel_report(self, report_lines):
		filename = 'Sumas y Saldos.xls'
		workbook = xlwt.Workbook(style_compression=2)
		worksheet = workbook.add_sheet('Sumas y Saldos', cell_overwrite_ok=True)
		title = xlwt.easyxf("font:height 300,bold on,color black; align:horiz center,vert center; borders:left thin,right thin,top thin,bottom thin; pattern:pattern solid,fore_colour gray25")
		head = xlwt.easyxf("font:bold on,color black; align:horiz center,vert center; borders:left thin,right thin,top thin,bottom thin; pattern:pattern solid,fore_colour gray25")
		cell = xlwt.easyxf("font:color black; borders:left thin,right thin,top thin,bottom thin")
		detail = xlwt.easyxf("font:italic on,color black; borders:left thin,right thin,top thin,bottom thin")
		money = xlwt.easyxf("font:color black; align:horiz right; borders:left thin,right thin,top thin,bottom thin", num_format_str='#,##0.00')
		detail_money = xlwt.easyxf("font:italic on,color black; align:horiz right; borders:left thin,right thin,top thin,bottom thin", num_format_str='#,##0.00')
		worksheet.col(0).width = 4200; worksheet.col(1).width = 13000
		worksheet.col(2).width = 5000; worksheet.col(3).width = 5000; worksheet.col(4).width = 5000
		worksheet.row(0).height = 600
		worksheet.write_merge(0, 0, 0, 4, self.company_id.name + ' : SUMAS Y SALDOS', title)
		filters = []
		filters.append('Movimientos: ' + ('Publicados' if self.target_move == 'posted' else 'Todos'))
		if self.date_from: filters.append('Desde: %s' % self.date_from)
		if self.date_to: filters.append('Hasta: %s' % self.date_to)
		if self.sd_account_id: filters.append('Cuentas: %s' % ', '.join(self.sd_account_id.mapped('display_name')))
		if self.esi_analytic_account_ids: filters.append('Analítica: %s' % ', '.join(self.esi_analytic_account_ids.mapped('display_name')))
		if self.esi_partner_ids: filters.append('Empresa: %s' % ', '.join(self.esi_partner_ids.mapped('display_name')))
		if self.esi_cash_flow_ids: filters.append('CTA Flujo: %s' % ', '.join(self.esi_cash_flow_ids.mapped('display_name')))
		worksheet.write_merge(1, 1, 0, 4, ' | '.join(filters), cell)
		for c, h in enumerate(['Código', 'Cuenta', 'Débito', 'Crédito', 'Balance']): worksheet.write(3, c, h, head)
		row = 4
		for line in report_lines:
			is_detail = bool(line.get('esi_detail'))
			text_style = detail if is_detail else cell
			num_style = detail_money if is_detail else money
			worksheet.write(row, 0, line.get('code') or '', text_style)
			name = ('     ↳ ' if is_detail else '') + (line.get('name') or '')
			worksheet.write(row, 1, name, text_style)
			worksheet.write(row, 2, line.get('debit') or 0.0, num_style)
			worksheet.write(row, 3, line.get('credit') or 0.0, num_style)
			worksheet.write(row, 4, line.get('balance') or 0.0, num_style)
			row += 1
		fp = io.BytesIO(); workbook.save(fp)
		export_id = self.env['excel.report'].create({'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
		return {'view_mode':'form','res_id':export_id.id,'res_model':'excel.report','view_type':'form','type':'ir.actions.act_window','target':'new'}

	def print_trial_balance(self):
		res = super(AccountingReportBi, self).print_trial_balance()
		if self._context.get('report_type') == 'excel':
			report_lines = res.get('data').get('account_res')
			return self._print_excel(report_lines, report_name='trial_balance')
		else:
			return res
