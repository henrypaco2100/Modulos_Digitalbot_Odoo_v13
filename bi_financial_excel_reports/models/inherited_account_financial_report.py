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

	def _print_general_ledger_excel_report(self,report_lines):
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
		# worksheet.col(0).width = 5500
		worksheet.col(1).width = 5500
		worksheet.col(2).width = 6500
		worksheet.col(3).width = 6500
		worksheet.col(4).width = 5500
		worksheet.col(5).width = 8000
		worksheet.write_merge(0, 0, 0, 8, self.env['res.users'].browse(self.env.uid).company_id.name + " : Informe del libro mayor ", style=style_header)
		worksheet.write_merge(1, 1, 0, 1, 'Diarios', style_line)
		worksheet.write(1, 2, 'Mostrar cuenta', style_line)
		worksheet.write(1, 3, 'Movimientos de destino', style_line)
		worksheet.write(1, 4, 'Ordenado por', style_line)
		if self.date_from:
			worksheet.write(1, 5, 'Fecha de', style_line)
		if self.date_to:
			worksheet.write_merge(1, 1, 6, 8, 'Fecha hasta', style_line)
			#DAVID

		style_line = xlwt.easyxf("font: height 150, color black; align: wrap yes; border: right thin, left thin, bottom thin")
		journals = self.journal_ids
		if journals and len(journals)>0:
			journals_id = ', '.join([lt.code or '' for lt in journals])
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

		style_line = xlwt.easyxf("font:color black; align: horiz center, vert center; border: right thin, left thin, bottom thin")
		if self.date_from:
			worksheet.write(2, 5, str(self.date_from), style_line)
		if self.date_to:
			worksheet.write_merge(2, 2, 6, 8, str(self.date_to), style_line)

		style_line = xlwt.easyxf("font:color black; align: horiz center; border: right thin, left thin, bottom thin; pattern: pattern solid, fore_colour gray25")
		worksheet.write(3, 0, 'Fecha', style_line)
		worksheet.write(3, 1, 'Diario', style_line)
		worksheet.write(3, 2, 'Asociado', style_line)
		worksheet.write(3, 3, 'Ref', style_line)
		worksheet.write(3, 4, 'Asiento', style_line)
		worksheet.write(3, 5, 'Etiqueta de entrada', style_line)
		worksheet.write(3, 6, 'Débito', style_line)
		worksheet.write(3, 7, 'Crédito', style_line)
		worksheet.write(3, 8, 'Balance', style_line)
		row = 4
		col = 0

		for line in report_lines:
			# row += 1
			style_line = xlwt.easyxf("font: bold on, color black; border: right thin, left thin, bottom thin, top thin")
			flag = False
			worksheet.write_merge(row, row, 0, 5, line.get('code') + line.get('name').upper(), style=style_line)
			worksheet.write(row, col + 6, line.get('debit'), style=style_line)
			worksheet.write(row, col + 7, line.get('credit'), style=style_line)
			worksheet.write(row, col + 8, line.get('balance'), style=style_line)
			row += 1
			for move_line in line.get('move_lines'):
				style_line = xlwt.easyxf("font:color black; border: right thin, left thin, bottom thin, top thin")
				worksheet.write(row, col, str(move_line.get('ldate')),style_line)
				worksheet.write(row, col + 1, move_line.get('lcode'), style_line)
				worksheet.write(row, col + 2, move_line.get('partner_name'), style_line)
				worksheet.write(row, col + 3, move_line.get('lref'), style_line)
				worksheet.write(row, col + 4, move_line.get('move_name'), style_line)
				worksheet.write(row, col + 5, move_line.get('lname'), style_line)
				worksheet.write(row, col + 6, move_line.get('debit'), style_line)
				worksheet.write(row, col + 7, move_line.get('credit'), style_line)
				worksheet.write(row, col + 8, move_line.get('balance'), style_line)
				flag = True
				row += 1
			if not flag:
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

	def print_general_ledger(self):
		res = super(AccountingReportBi, self).print_general_ledger()
		if self._context.get('report_type') == 'excel':
			report_lines = res.get('data').get('Account')
			return self._print_excel(report_lines,report_name='general_ledger')
		else:
			return res

	def _print_trial_balance_excel_report(self,report_lines):
		filename = 'Balance General.xls'
		workbook = xlwt.Workbook()
		worksheet = workbook.add_sheet('Sheet 1')
		date_format = xlwt.XFStyle()
		date_format.num_format_str = 'dd/mm/yyyy'
		style_header = xlwt.easyxf(
			"font:height 300; font: name Liberation Sans, bold on,color black; align: horiz center")
		style_line = xlwt.easyxf(
			"font:bold on,color black;")
		worksheet.row(0).height_mismatch = True
		worksheet.row(0).height = 800
		worksheet.col(0).width = 3900
		worksheet.col(1).width = 5500
		worksheet.col(2).width = 5500
		worksheet.col(3).width = 5500
		worksheet.col(4).width = 5500
		worksheet.col(5).width = 5500
		worksheet.write_merge(0, 0, 0, 5, self.env['res.users'].browse(self.env.uid).company_id.name + " : Informe de balance de comprobación ", style=style_header)
		worksheet.write(2,0,'Mostrar cuenta')
		worksheet.write(2,1,'Movimientos de destino')
		if self.date_from:
			worksheet.write(2, 2, 'Fecha de')
		if self.date_to:
			worksheet.write(2, 3, 'Fecha hasta')
		if self.display_account == 'all':
			display_account = 'Todas las cuentas'
		elif self.display_account == 'movement':
			display_account = 'Con movimientos'
		else:
			display_account = 'Con saldo no igual a cero'
		worksheet.write(3,0,display_account)
		worksheet.write(3,1,'Todas las entradas publicadas' if self.target_move == 'posted' else 'Todas las entradas')
		if self.date_from:
			worksheet.write(3, 2, self.date_from,date_format)
		if self.date_to:
			worksheet.write(3, 3, self.date_to,date_format)

		worksheet.write(4,0,'Código')
		worksheet.write(4,1,'Cuenta')
		worksheet.write(4,2,'Débito')
		worksheet.write(4,3,'Crédito')
		worksheet.write(4,4,'Balance')
		row = 5
		col = 0
		for lines in report_lines:
			worksheet.write(row,col,lines.get('code'))
			worksheet.write(row,col+1,lines.get('name'))
			worksheet.write(row,col+2,lines.get('debit'))
			worksheet.write(row,col+3,lines.get('credit'))
			worksheet.write(row,col+4,lines.get('balance'))
			row+=1
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

	def print_trial_balance(self):
		res = super(AccountingReportBi, self).print_trial_balance()
		if self._context.get('report_type') == 'excel':
			report_lines = res.get('data').get('account_res')
			return self._print_excel(report_lines, report_name='trial_balance')
		else:
			return res
