import datetime
import locale  # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from itertools import groupby
import xlwt
import base64
import io
import xlsxwriter

_logger = logging.getLogger(__name__)


class ReportByAuthor(models.Model):
    _name = 'report.by.author'

    # category_id = self.
    date_start = fields.Date(string="Fecha inicio", required=False)
    date_end = fields.Date(string="Fecha Final", required=False)
    categ_id = fields.Many2many('product.category', string="Categoria de Producto")
    product_id = fields.Many2many('product.product', string="Libro")
    autor_id = fields.Many2many('res.partner', string="Autor")

    sinvariantes = fields.Boolean(string="Separar variantes de productos", required=False)
    #sintransferenciasinternas = fields.Boolean(string="Incluir trasnferencias internas", required=False)
    filtraralmacenes = fields.Boolean(string="Agrupar almacenes", required=False, default=True)
    filtrarcategorias = fields.Boolean(string="Agrupar categorias", required=False)
    filtrartipomov = fields.Boolean(string="tipo/concepto", required=False, default=True)
    filtrarproductos = fields.Boolean(string="Filtrar productos", required=False)
    mostrar_ubicaciones = fields.Boolean(string="Mostrar ubicaciones origen/destino", required=False, default=True)

    seleccionalmacenes = fields.Many2many('stock.warehouse', string="Seleccion de almacenes")
    # seleccionproductos = fields.Many2many('product.product', string="Seleccion de productos")

    excel_file = fields.Binary('Reporte Excel')
    file_name = fields.Char('Archivo Excel', size=64)

    def action_report_kardex(self):
        reporte = self._imprimir_xls_reporte_kardex()
        return reporte
    # METODO PARA IMPRIMIR EN EXCEL

    def _imprimir_xls_reporte_kardex(self):
        reporte = xlwt.Workbook(style_compression=2)
        worksheet1 = reporte.add_sheet('sheet_1', cell_overwrite_ok=True)
        worksheet1.set_portrait(False)
        # IMPRIMIR CABECERA DEL REPORTE -----------------------------------------------------
        style_header = xlwt.easyxf("font: name Calibri, height 250, color black, bold on, height 240; align: vert center,horiz center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour grey25")
        columnkardex = 13
        if not self.filtrartipomov: columnkardex -= 1
        if self.mostrar_ubicaciones: columnkardex += 2
        worksheet1.write_merge(0, 1, 0, 9, 'INFORME POR VENTA DE PUBLICACIONES', style_header)

        style_header = xlwt.easyxf("font: name Calibri, height 130, color black, bold on; align: vert center,horiz center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour gray25")
        worksheet1.write_merge(4, 5, 0, 0, 'Nro', style_header)
        worksheet1.write_merge(4, 5, 1, 1, 'TITULO', style_header)
        worksheet1.write_merge(4, 5, 2, 2, 'CANTIDAD\nRECIBIDA', style_header)
        worksheet1.write_merge(4, 5, 3, 3, 'CANTIDAD\nDEVUELTA', style_header)
        worksheet1.write_merge(4, 5, 4, 4, 'DEPOSITO\nLEGAL', style_header)
        worksheet1.write_merge(4, 5, 5, 5, 'TOTAL\nVENTAS\nREALIZADAS', style_header)
        worksheet1.write_merge(4, 5, 6, 6, 'PVP', style_header)
        worksheet1.write_merge(4, 5, 7, 7, 'PRECIO\nACUERDO\nCONTRATO', style_header)
        worksheet1.write_merge(4, 5, 8, 8, 'TOTAL\nVENTAS Bs', style_header)
        worksheet1.write_merge(4, 5, 9, 9, 'SALDO EN\nCONSIG. O\nALMACEN', style_header)

        # RELLENAR REPORTE KARDEX CON MOVIMIENTO DE EXISTENCIAS ----------------------------------
        worksheet1.row(4).height = 300
        worksheet1.col(0).width = 1500
        worksheet1.col(1).width = 12000
        worksheet1.col(2).width = 2500
        worksheet1.col(3).width = 2500
        worksheet1.col(4).width = 2500
        worksheet1.col(5).width = 2500
        worksheet1.col(6).width = 2500
        worksheet1.col(7).width = 2500
        worksheet1.col(8).width = 2500
        worksheet1.col(9).width = 2500

        kardex_autores = self.datos_kardex(self.date_start, self.date_end)

        totalrows = 0
        for autor in kardex_autores:
            totalrows += 1
            for libro in autor["Array_Libros"]:
                totalrows += 1
        totalrows += 1

        for i in range(totalrows):
            for j in range(10):
                worksheet1.write((i + 6), j, "", xlwt.easyxf("borders: left thin, right thin, bottom thin"))
                if j == 5:
                    worksheet1.write((i + 6), j, "", xlwt.easyxf("borders: left thin, right thin, bottom thin; pattern: pattern solid, fore_colour lime"))
                if i == totalrows - 1:
                    worksheet1.write((i + 6), j, "", xlwt.easyxf("borders: left thin, right thin, bottom thin; pattern: pattern solid, fore_colour gray25"))

        # RELLENAMOS CABECERA
        worksheet1.row(3).height = 500
        style_header = xlwt.easyxf(
            "font: name Calibri, height 150, color black, bold on; align: horiz left; borders: left thin, right thin")
        fecha_inicio = 'primer registro'
        fecha_fin = 'fecha actual'
        if self.date_start:
            fecha_inicio = str(self.date_start)
        if self.date_end:
            fecha_fin = str(self.date_end)
        worksheet1.write_merge(2, 2, 0, 1, 'Seleccion Libros: ', style_header)
        worksheet1.write_merge(2, 2, 3, 5, 'fecha:', style_header)
        worksheet1.write(2, 2, 'Compañia:', style_header)
        worksheet1.write_merge(2, 2, 6, 9, 'Seleccion Autores: ', style_header)

        lista_libros = ''
        i = 0
        for libro in self.product_id:
            i += 1
            if i == len(self.product_id):
                lista_libros += libro.name
            else:
                lista_libros += libro.name + ', '

        lista_autores = ''
        i = 0
        for autor in self.autor_id:
            i += 1
            if i == len(self.autor_id):
                lista_autores += autor.name
            else:
                lista_autores += autor.name + ', '

        worksheet1.write_merge(3, 3, 3, 5, fecha_inicio + " - " + fecha_fin, xlwt.easyxf(
            "font: name Calibri, height 150, color black; align: vert top,horiz left; borders: left thin, right thin"))
        worksheet1.write(3, 2, self.env.user.company_id.name, xlwt.easyxf(
            "font: name Calibri, height 150, color black; align: vert top, horiz left; borders: left thin, right thin"))
        worksheet1.write_merge(3, 3, 0, 1, lista_libros, xlwt.easyxf(
            "font: name Calibri, height 150, color black; align: vert top, horiz left; borders: left thin, right thin"))
        worksheet1.write_merge(3, 3, 6, 9, lista_autores, xlwt.easyxf(
            "font: name Calibri, height 150, color black; align: vert top, horiz left; borders: left thin, right thin"))

        # SUMAMOS INDEX PARA HACER ESPACIO PARA EL PRODUCTO (PARCHE :( )
        style_autor = xlwt.easyxf("font: name Calibri, height 150, color black, bold on; align: horiz left; borders: left thin, right thin, bottom thin")  # ; pattern: pattern solid, fore_colour lavender
        indexrow = 6
        total_ventas_cant = 0
        total_ventas_bs = 0
        total_res_almacen = 0
        for autor in kardex_autores:
            nro = 1
            worksheet1.write(indexrow, 1, autor["Autor"], style_autor)
            indexrow += 1
            for libro in autor["Array_Libros"]:
                style_kardex = xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz left; borders: left thin, right thin, bottom thin")
                worksheet1.write(indexrow, 1, libro["Libro"], style_kardex)
                worksheet1.write(indexrow, 0, str(nro), xlwt.easyxf("font: name Calibri, height 200, color black, bold on; align: horiz center; borders: left thin, right thin, bottom thin"))
                nro += 1
                quantity_res = self.env['stock.quant'].search([('product_id', '=', libro["product_id"]), ('location_id.usage', '=', 'internal')])
                res_almacen = sum(quantity_res.mapped('quantity'))
                # print('cantidad en stock ', libro["Libro"].name, ": ", res_almacen)
                worksheet1.write(indexrow, 2, str(0), xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz center; borders: left thin, right thin, bottom thin"))
                worksheet1.write(indexrow, 3, str(0), xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz center; borders: left thin, right thin, bottom thin"))
                worksheet1.write(indexrow, 4, str(0), xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz center; borders: left thin, right thin, bottom thin"))

                worksheet1.write(indexrow, 5, str(libro["cant_realizada"]), xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz center; borders: left thin, right thin, bottom thin; pattern: pattern solid, fore_colour lime"))
                worksheet1.write(indexrow, 6, str(libro["pvp"]), xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz right; borders: left thin, right thin, bottom thin"))
                worksheet1.write(indexrow, 7, str(libro["precio_impuesto"]), xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz right; borders: left thin, right thin, bottom thin"))
                worksheet1.write(indexrow, 8, str(libro["cant_realizada"] * libro["precio_impuesto"]), xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz right; borders: left thin, right thin, bottom thin"))
                worksheet1.write(indexrow, 9, str(res_almacen), xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz center; borders: left thin, right thin, bottom thin"))

                total_ventas_cant += libro["cant_realizada"]
                total_ventas_bs += libro["precio_impuesto"] * libro["cant_realizada"]
                total_res_almacen += res_almacen
                indexrow += 1

        worksheet1.write(indexrow, 1, "TOTALES", xlwt.easyxf("font: name Calibri, height 200, color black, bold on; align: horiz center; borders: left thin, right thin, bottom thin; pattern: pattern solid, fore_colour gray25"))
        worksheet1.write(indexrow, 5, str(total_ventas_cant), xlwt.easyxf("font: name Calibri, height 200, color black, bold on; align: horiz center; borders: left thin, right thin, bottom thin; pattern: pattern solid, fore_colour gray25"))
        worksheet1.write(indexrow, 8, str(total_ventas_bs), xlwt.easyxf("font: name Calibri, height 200, color black, bold on; align: horiz right; borders: left thin, right thin, bottom thin; pattern: pattern solid, fore_colour gray25"))
        worksheet1.write(indexrow, 9, str(total_res_almacen), xlwt.easyxf("font: name Calibri, height 200, color black, bold on; align: horiz center; borders: left thin, right thin, bottom thin; pattern: pattern solid, fore_colour gray25"))

        # GUARDAR REPORTE EXCEL-------------------------------------------------------------
        fp = io.BytesIO()
        reporte.save(fp)
        # datos_report = self.datos_kardex()
        self.write({'excel_file': base64.encodestring(fp.getvalue()), 'file_name': 'INFORME POR VENTA DE PUBLICACIONES.xls'})
        res = {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'report.by.author',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res

    def datos_kardex(self, date_start, date_end):
        date_conditions = self.construct_date_conditions(date_start, date_end)

        query = """
            SELECT
                am.id AS invoice_id,
                aml.id AS invoice_line_id,
                aml.product_id,
                pt.sd_autor_id,
                pt.list_price,
                pt.sd_amount_impuesto,
                am.invoice_date,
                aml.quantity,
                pt.name AS product_name,
                rp.name AS autor_name
            FROM
                account_move am
            JOIN
                account_move_line aml ON am.id = aml.move_id
            JOIN
                product_product pp ON aml.product_id = pp.id
            JOIN
                product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN
                res_partner rp ON pt.sd_autor_id = rp.id
            WHERE
                am.state = 'posted'
                AND am.type = 'out_invoice'
                {date_conditions}
            ORDER BY
                am.invoice_date ASC
        """.format(date_conditions=date_conditions)

        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()
        # print('result : ', results)
        array_product_ids = []
        array_autor_ids = []
        kardex_autores = []
        for autor in self.autor_id:
            array_autor_ids.append(autor.id)
        for producto in self.product_id:
            array_product_ids.append(producto.id)
        for linea in results:
            if linea["sd_autor_id"] is not None:
                if linea["sd_autor_id"] in array_autor_ids or linea["product_id"] in array_product_ids:
                    # print('results: ', linea)

                    index_autor = 0
                    nuevo = True
                    for autor in kardex_autores:
                        if linea["autor_name"] == autor["Autor"]:
                            index_libro = 0
                            for libro in autor["Array_Libros"]:
                                if linea["product_name"] == libro["Libro"]:
                                    nuevo = False
                                    kardex_autores[index_autor]["Array_Libros"][index_libro]["cant_realizada"] += linea["quantity"]
                                    break
                                index_libro += 1
                            if nuevo:
                                nuevo = False
                                kardex_autores[index_autor]["Array_Libros"].append({"Libro": linea["product_name"], "pvp": linea["list_price"], "precio_impuesto": linea["sd_amount_impuesto"], "cant_realizada": linea["quantity"], "product_id": linea["product_id"]})
                                break
                        index_autor += 1
                    if nuevo:
                        kardex_autores.append({"Autor": linea["autor_name"], "Array_Libros": [{"Libro": linea["product_name"], "pvp": linea["list_price"], "precio_impuesto": linea["sd_amount_impuesto"], "cant_realizada": linea["quantity"], "product_id": linea["product_id"]}]})
        # print('kardex autores: ', kardex_autores)
        # Rest of your processing logic

        return kardex_autores

    def construct_date_conditions(self, date_start, date_end):
        conditions = []

        if date_start:
            conditions.append(f"am.invoice_date >= '{date_start}'")

        if date_end:
            conditions.append(f"am.invoice_date <= '{date_end}'")

        if conditions:
            return "AND " + " AND ".join(conditions)
        else:
            return ""

    def rango_consulta(self, date_start, date_end):
        """
        rango de fechas stock.move
        """

        if date_start and date_end:
            consulta_fecha_inicio = ('date', '>=', date_start)
            consulta_fecha_fin = ('date', '<=', date_end)
            return consulta_fecha_inicio, consulta_fecha_fin
        else:
            if date_start or date_end:
                if date_start:
                    consulta_fecha_inicio = ('date', '>=', date_start)
                    return consulta_fecha_inicio, ('date','!=', None)
                else:
                    consulta_fecha_fin = ('date', '<=', date_end)
                    return ('date','!=', None),consulta_fecha_fin
            return ('date','!=', None), ('date','!=', None)

