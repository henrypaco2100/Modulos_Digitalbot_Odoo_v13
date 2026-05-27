# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import xlwt
import base64
import io
_logger = logging.getLogger(__name__)


class AccountReport(models.Model):
    _name = 'account.report'
    _rec_name = 'name'
    _description = 'New Description'
    name = fields.Char()
    date_start = fields.Date(string="Fecha inicio", required=True)
    date_end = fields.Date(string="Fecha de fin", required=True)
    report_lines_ids = fields.One2many(comodel_name="report.lines",
                                       inverse_name="account_report_id",
                                       string="Report Lines")
    # print_xlsx = fields.Many2one('report.st_price_cost_report.product_xlsx')

    def set_origin(self):
        self.report_lines_ids.unlink()

        sale_order = self.env['sale.order'].search([('state', '=', 'sale'),
                                                    ('date_order', '>=', self.date_start),
                                                    ('date_order', '<=', self.date_end)])

        if sale_order and len(sale_order) >= 1:

            report_val = []
            report_lines = []
            for line in sale_order:
                product = line.order_line

                stock_picking = self.env['stock.picking'].search([
                    ('origin', '=', line.name),
                    ('scheduled_date', '>=', self.date_start),
                    ('scheduled_date', '<=', self.date_end),
                    ('state', '!=', 'cancel')
                ])

                        # for move in stock.move_ids_without_package:
                        # for valuation in valuations:
                        # if line.name == stock.origin and stock.name:
                            # if line.order_id.name == stock.origin and stock.name in valuation.description:
                for t in product:
                    valuations = self.env['stock.valuation.layer'].search(
                        [('product_id', '=', t.product_id.id),
                         ('stock_move_id.picking_id.sale_id.name', '=', line.name),
                         ('stock_move_id.state', '=', 'done'),
                         ('unit_cost', '!=', 0.0)], limit=1)
                    """TODO: SE NECESITA IMPRIMIR UN WARNING EN ESTE PASO PARA EL CLIENTE"""
                    nombres_de_Facturas = [invoice_id.name for invoice_id in line.invoice_ids]
                    val = {
                        'name': line.name or ' ',
                        'name_fact': nombres_de_Facturas or ' ',
                        'name_stock': stock_picking.name or ' ',
                        'cliente': line.partner_id.name or ' ',
                        'invoice_date': str(line.date_order) or ' ',
                        'deliver_date': str(stock_picking.date_done) or ' ',
                        # 'journal_id': valuations.account_move_id.name or ' ',
                        'product': t.product_id.name or ' ',
                        'description': t.product_id.name or ' ',
                        'quantity': t.product_uom_qty or ' ',
                        'quantity_invoiced': t.qty_invoiced or ' ',
                        # 'quantity_done': t.order_id.picking_ids.move_ids_without_package.quantity_done or ' ',
                        'stock_pick_type': stock_picking.picking_type_id.name or ' ',
                        'location': stock_picking.location_id.name or ' ',
                        'location_dest_id': stock_picking.location_dest_id.name or ' ',
                        # 'location_dest_id': stock.location_dest_id.name or ' ',
                        # 'price_unit': t.price_unit or ' ',
                        # 'valuation_cost': valuations.unit_cost or ' ',
                        'price_subtotal': t.price_subtotal or ' ',
                        'value': str(valuations.value) or ' ',
                        'utility': str(t.price_subtotal - abs(valuations.value))
                    }
                    if val not in report_val:
                        report_val.append(val)

            for record in report_val:
                report_lines.append((0, 0, record))

            for record in self:
                record.report_lines_ids = report_lines
                return self.env.ref('st_price_cost_report.account_product_report_pdf').report_action(self)
        else:
            raise UserError(_('Para poder imprimir el reporte necesita que el pedido de venta este EN EL ESTADO VALIDADO.'))

    def print_excel(self):

        self.report_lines_ids.unlink()

        sale_order = self.env['sale.order'].search([('state', '=', 'sale'),
                                                    ('date_order', '>=', self.date_start),
                                                    ('date_order', '<=', self.date_end)])

        if sale_order and len(sale_order) >= 1:

            report_val = []
            report_lines = []
            for line in sale_order:
                product = line.order_line

                stock_picking = self.env['stock.picking'].search([
                    ('origin', '=', line.name),
                    ('scheduled_date', '>=', self.date_start),
                    ('scheduled_date', '<=', self.date_end),
                    ('state', '!=', 'cancel')
                ])

                # for move in stock.move_ids_without_package:
                # for valuation in valuations:
                # if line.name == stock.origin and stock.name:
                # if line.order_id.name == stock.origin and stock.name in valuation.description:
                for t in product:

                    valuations = self.env['stock.valuation.layer'].search(
                        [('product_id', '=', t.product_id.id),
                         ('stock_move_id.picking_id.sale_id.name', '=', line.name),
                         ('stock_move_id.state', '=', 'done'),
                         ('unit_cost', '!=', 0.0)], limit=1)
                    # if valuations and len(valuations) > 1:
                    """TODO: SE NECESITA IMPRIMIR UN WARNING EN ESTE PASO PARA EL CLIENTE"""
                    nombres_de_Facturas = [invoice_id.name for invoice_id in line.invoice_ids]
                    val = {
                        'name': line.name or ' ',
                        'name_fact': nombres_de_Facturas or ' ',
                        'name_stock': stock_picking.name or ' ',
                        'cliente': line.partner_id.name or ' ',
                        'invoice_date': str(line.date_order) or ' ',
                        'deliver_date': str(stock_picking.date_done) or ' ',
                        # 'journal_id': valuations.account_move_id.name or ' ',
                        'product': t.product_id.name or ' ',
                        'description': t.product_id.name or ' ',
                        'quantity': t.product_uom_qty or ' ',
                        'quantity_invoiced': t.qty_invoiced or ' ',
                        # 'quantity_done': t.order_id.picking_ids.move_ids_without_package.quantity_done or ' ',
                        'stock_pick_type': stock_picking.picking_type_id.name or ' ',
                        'location': stock_picking.location_id.name or ' ',
                        'location_dest_id': stock_picking.location_dest_id.name or ' ',
                        # 'location_dest_id': stock.location_dest_id.name or ' ',
                        # 'price_unit': t.price_unit or ' ',
                        # 'valuation_cost': valuations.unit_cost or ' ',
                        'price_subtotal': t.price_subtotal or ' ',
                        'value': str(valuations.value) or ' ',
                        'utility': str(t.price_subtotal - abs(valuations.value))
                    }
                    if val not in report_val:
                        report_val.append(val)

            for record in report_val:
                report_lines.append((0, 0, record))

            for record in self:
                record.report_lines_ids = report_lines
                return self.generate_xlsx_report(self.report_lines_ids)
        else:
            raise UserError(_('Para poder imprimir el reporte necesita que el pedido de venta este el estado VALIDADO.'))
            # return self.generate_xlsx_report(self.report_lines_ids)

    def generate_xlsx_report(self, report):
        report_name = str('INFORME DE VENTAS PRECIO COSTO')
        report_name += '.xls'
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        # sheet = workbook.add_worksheet(report_name[:31])
        # bold = workbook.add_format({'bold': True})
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'
        style_header = xlwt.easyxf(
            "font:height 300; font: name Liberation Sans, bold on,color black; align: horiz center")
        worksheet.row(0).height_mismatch = True
        worksheet.row(0).height = 500
        worksheet.col(0).width = 5700
        worksheet.col(1).width = 8000
        worksheet.col(2).width = 8000
        worksheet.col(3).width = 6500
        worksheet.col(4).width = 6000
        worksheet.col(5).width = 6000
        worksheet.col(6).width = 7500
        worksheet.col(7).width = 8000
        worksheet.col(8).width = 7500
        worksheet.col(9).width = 7500
        worksheet.col(10).width = 7500
        worksheet.col(11).width = 7500
        worksheet.col(12).width = 7500
        worksheet.col(13).width = 5500
        worksheet.col(14).width = 5500
        worksheet.col(15).width = 5500
        worksheet.col(16).width = 5500
        worksheet.col(17).width = 5500
        worksheet.row(3).height = 400
        worksheet.row(15).height = 300
        worksheet.row(16).height = 300
        worksheet.row(18).height = 300
        worksheet.write_merge(0, 0, 0, 5, 'INFORME DE VENTAS PRECIO COSTO', style_header)
        # worksheet.write(0, 1, report.name)
        worksheet.write(1, 0, 'DEL', date_format)
        worksheet.write(1, 1, self.date_start, date_format)
        worksheet.write(2, 0, 'AL', date_format)
        worksheet.write(2, 1, self.date_end, date_format)
        row = 3
        col = 0
        #cabecera
        style_line = xlwt.easyxf(
            "font:height 280; font:bold on,color blue;")
        worksheet.write(row, col, 'Pedido de Venta', style_line)
        worksheet.write(row, col + 1, 'Codigo de Factura', style_line)
        # worksheet.write(row, col, 'Pedido de Venta', style_line)
        # worksheet.write_merge(row, col, len('Pedido de Venta') + 2)
        worksheet.write(row, col + 2, 'Documento de Entrega', style_line)
        # worksheet.write_merge(row, col, len('Documento de Entrega') + 2)
        worksheet.write(row, col + 3, 'Cliente', style_line)
        # worksheet.write_merge(row, col + 2, len('Cliente') + 10)
        worksheet.write(row, col + 4, 'Fecha de Orden', style_line)
        # worksheet.write_merge(row, col + 3, len('Fecha de Orden') + 2)
        worksheet.write(row, col + 5, 'Fecha Entregada', style_line)
        # worksheet.write_merge(row, col + 4, len('Fecha Entregada') + 2)
        # worksheet.write(row, col + 5, 'Diario de Entrega', style_line)
        # worksheet.write_merge(row, col + 5, len('Diario de Entrega') + 2)
        worksheet.write(row, col + 6, 'Producto', style_line)
        # worksheet.write_merge(row, col + 6, len('Producto') + 2)
        worksheet.write(row, col + 7, 'Descripcion Producto', style_line)
        # worksheet.write_merge(row, col + 7, len('Descripcion Producto') + 2)
        worksheet.write(row, col + 8, 'Cantidad', style_line)
        # worksheet.write_merge(row, col + 8, len('Cantidad') + 2)
        worksheet.write(row, col + 9, 'Cantidad Facturada', style_line)
        # worksheet.write_merge(row, col + 9, len('Cantidad Facturada') + 2)
        # worksheet.write(row, col + 9, 'Cantidad Entregada', style_line)
        # worksheet.write_merge(row, col + 10, len('Cantidad Entregada') + 2)
        worksheet.write(row, col + 10, 'Operación de Entrega', style_line)
        # worksheet.write_merge(row, col + 11, len('Operación de Entrega') + 2)
        worksheet.write(row, col + 11, 'Ubicación de Origen', style_line)
        worksheet.write(row, col + 12, 'Ubicación de Destino', style_line)
        # worksheet.write_merge(row, col + 12, len('Ubicación de Origen') + 2)
        # worksheet.write(row, col + 12, 'Precio Unitario', style_line)
        # worksheet.write_merge(row, col + 13, len('Precio Unitario') + 2)
        # worksheet.write(row, col + 13, 'Precio Unitario', style_line)
        # worksheet.write_merge(row, col + 14, len('Costo Unitario') + 2)
        worksheet.write(row, col + 13, 'Sub Total', style_line)
        # worksheet.write_merge(row, col + 16, len('Sub Total') + 2)
        worksheet.write(row, col + 14, 'Costo Total', style_line)
        # worksheet.write_merge(row, col + 17, len('Costo Total') + 2)
        row = 4
        col = 0
        for record in report:
            for line in record:
                worksheet.write(row, col, line.name)
                worksheet.write(row, col + 1, line.name_fact)
                worksheet.write(row, col + 2, line.name_stock)
                worksheet.write(row, col + 3, line.cliente)
                worksheet.write(row, col + 4, line.invoice_date)
                worksheet.write(row, col + 5, line.deliver_date)
                # worksheet.write(row, col + 5, line.journal_id)
                worksheet.write(row, col + 6, line.product)
                worksheet.write(row, col + 7, line.description)
                worksheet.write(row, col + 8, line.quantity)
                worksheet.write(row, col + 9, line.quantity_invoiced)
                # worksheet.write(row, col + 9, line.quantity_done)
                worksheet.write(row, col + 10, line.stock_pick_type)
                worksheet.write(row, col + 11, line.location)
                worksheet.write(row, col + 12, line.location_dest_id)
                # worksheet.write(row, col + 12, line.valuation_cost)
                # worksheet.write(row, col + 13, line.price_unit)
                worksheet.write(row, col + 13, line.price_subtotal)
                worksheet.write(row, col + 14, line.value)
                row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        export_id = self.env['excel.report'].create(
            {'excel_file': base64.encodestring(fp.getvalue()), 'file_name': report_name})
        res = {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'excel.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res


class ReportLines(models.Model):
    _name = 'report.lines'
    _rec_name = 'name'
    _description = 'New Description'

    account_report_id = fields.Many2one(comodel_name="account.report",
                                        string="Account Report", required=False, )
    name = fields.Char('Pedio de Venta')
    name_fact = fields.Char('Factura')
    invoice_origin = fields.Char('Origen de factura')
    name_stock = fields.Char('Documento de entrega')
    cliente = fields.Char('Cliente')
    referencia = fields.Char('Referencia')
    invoice_date = fields.Char('Fecha Factura')
    deliver_date = fields.Char('Fecha de entrega')
    journal_id = fields.Char('Diario de Entrega')
    product = fields.Char('Producto')
    description = fields.Char('Description')
    quantity = fields.Float('Cantidad')
    quantity_invoiced = fields.Float('Cantidad Facturada')
    quantity_done = fields.Float('Cantidad Entregada')
    stock_pick_type = fields.Char('Tipo Operacion')
    location = fields.Char('Ubicacion de Origen')
    location_dest_id = fields.Char('Ubicacion de Destino')
    valuation_cost = fields.Float('Costo Unitario')
    price_unit = fields.Float('Precio unitario')
    tax_id = fields.Char('Impuesto')
    price_subtotal = fields.Float('Sub total')
    value = fields.Float('Costo Total')
    utility = fields.Float('Utilidad')









