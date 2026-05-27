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
from datetime import datetime, time, timedelta
import xlsxwriter

_logger = logging.getLogger(__name__)


class KardexReport(models.Model):
    _name = 'kardex.report'

    # category_id = self.
    date_start = fields.Date(string="Fecha inicio", required=False)
    date_end = fields.Date(string="Fecha Final", required=False)
    categ_id = fields.Many2many('product.category', string="Categoria de Producto")

    sinvariantes = fields.Boolean(string="Separar variantes de productos", required=False)
    #sintransferenciasinternas = fields.Boolean(string="Incluir trasnferencias internas", required=False)
    filtraralmacenes = fields.Boolean(string="Agrupar almacenes", required=False, default=False)
    filtrarcategorias = fields.Boolean(string="Agrupar categorias", required=False)
    filtrartipomov = fields.Boolean(string="tipo/concepto", required=False, default=False,readonly=True)
    filtrarproductos = fields.Boolean(string="Filtrar productos", required=False)
    mostrar_ubicaciones = fields.Boolean(string="Mostrar ubicaciones origen/destino", required=False, default=False,readonly=True)
    sd_notdetails =  fields.Boolean(string="Detalles de movimientos", required=False, default=False)
    sd_notdocuments = fields.Boolean(string="Documento Origen", required=False, default=False,readonly=True)

    seleccionalmacenes = fields.Many2many('stock.warehouse', string="Seleccion de almacenes")
    seleccionproductos = fields.Many2many('product.product', string="Seleccion de productos")

    excel_file = fields.Binary('Reporte Excel')
    file_name = fields.Char('Archivo Excel', size=64)

    @api.onchange('sd_notdetails')
    def change_details(self):
        if self.sd_notdetails:
            self.sd_notdocuments= True
            self.mostrar_ubicaciones= True
            self.filtrartipomov = True
        else:
            self.sd_notdocuments = False
            self.mostrar_ubicaciones = False
            self.filtrartipomov = False
    def action_report_kardex(self):
        reporte = self._imprimir_xls_reporte_kardex()
        return reporte
    # METODO PARA IMPRIMIR EN EXCEL

    def _imprimir_xls_reporte_kardex(self):
        
        reporte = xlwt.Workbook(style_compression=2)
        worksheet1 = reporte.add_sheet('sheet_1', cell_overwrite_ok=True)
        # IMPRIMIR CABECERA DEL REPORTE -----------------------------------------------------
        style_header = xlwt.easyxf("font: name Calibri, height 250, color black, bold on, height 240; align: vert center,horiz center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour grey25")
        if not self.sd_notdetails:
            self.filtrartipomov = False
            self.mostrar_ubicaciones = False
            self.sd_notdocuments = False
        else:
            self.filtrartipomov = True
            self.mostrar_ubicaciones = True
            self.sd_notdocuments = True
        columnkardex = 13
        if not self.filtrartipomov: columnkardex -= 1
        if self.sd_notdocuments: columnkardex += 1
        if self.mostrar_ubicaciones: columnkardex += 2
        worksheet1.write_merge(0, 1, 0, columnkardex, 'REPORTE KARDEX - POR ALMACEN', style_header)

        style_header = xlwt.easyxf("font: name Calibri, height 200, color black, bold on; align: vert center,horiz center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour gray25")
        worksheet1.write_merge(4, 5, 0, 0, 'Nro', style_header)
        worksheet1.write_merge(4, 5, 1, 1, 'FECHA', style_header)
        worksheet1.write_merge(4, 5, 2, 2, 'CATEGORIA', style_header)
        indextipomov = 3
        if self.filtrartipomov:
            worksheet1.write_merge(4, 5, indextipomov, indextipomov, 'CONCEPTO', style_header)
            indextipomov += 1
        if self.mostrar_ubicaciones:
            worksheet1.write_merge(4, 5, indextipomov, indextipomov, 'ORIGEN', style_header)
            worksheet1.write_merge(4, 5, indextipomov + 1, indextipomov + 1, 'DESTINO', style_header)
            indextipomov += 2
        if self.sd_notdocuments:
            worksheet1.write_merge(4, 5, indextipomov, indextipomov, 'DOCUMENTO', style_header)
            indextipomov += 1

        #CODIGO PARA RECORRER LAS DEMAS COLUMNAS Y HACER ESPACIO PARA EL PRODUCTO
        worksheet1.write_merge(4, 5, indextipomov, indextipomov, 'PRODUCTO', style_header)
        indextipomov += 1


        style_header = xlwt.easyxf("font: name Calibri, height 200, color black, bold on; align: horiz center; borders: left thin, right thin, top thin; pattern: pattern solid, fore_colour gray25")
        style_header2 = xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz center; borders: right thin, left thin, bottom thin; pattern: pattern solid, fore_colour gray25")
        #style_header2 = xlwt.easyxf("font: color black; align: horiz center; borders: bottom thin; pattern: pattern solid, fore_colour gray25")
        #style_header3 = xlwt.easyxf("font: color black; align: horiz center; borders: right thin, left thin, bottom thin; pattern: pattern solid, fore_colour gray25")
        if self.sd_notdetails:
            worksheet1.write_merge(4, 4, indextipomov + 0, indextipomov + 2, 'ENTRADAS', style_header)
            worksheet1.write_merge(4, 4, indextipomov + 3, indextipomov + 5, 'SALIDAS', style_header)
            worksheet1.write_merge(4, 4, indextipomov + 6, indextipomov + 8, 'SALDOS', style_header)

            worksheet1.write(5, indextipomov + 0, 'CANTIDAD', style_header2)
            worksheet1.write(5, indextipomov + 1, 'VR UNITARIO', style_header2)
            worksheet1.write(5, indextipomov + 2, 'VR TOTAL', style_header2)
            worksheet1.write(5, indextipomov + 3, 'CANTIDAD', style_header2)
            worksheet1.write(5, indextipomov + 4, 'VR UNITARIO', style_header2)
            worksheet1.write(5, indextipomov + 5, 'VR TOTAL', style_header2)
            worksheet1.write(5, indextipomov + 6, 'CANTIDAD', style_header2)
            worksheet1.write(5, indextipomov + 7, 'VR UNITARIO', style_header2)
            worksheet1.write(5, indextipomov + 8, 'VR TOTAL', style_header2)
        else:
            worksheet1.write_merge(4, 4, indextipomov + 0, indextipomov + 2, 'SALDOS', style_header)
            worksheet1.write(5, indextipomov + 0, 'CANTIDAD', style_header2)
            worksheet1.write(5, indextipomov + 1, 'VR UNITARIO', style_header2)
            worksheet1.write(5, indextipomov + 2, 'VR TOTAL', style_header2)

        #RELLENAR REPORTE KARDEX CON MOVIMIENTO DE EXISTENCIAS ----------------------------------
        worksheet1.col(1).width = 5000
        indextipomov = 3
        if self.filtrartipomov:
            indextipomov += 1
            worksheet1.col(2).width = 7000

        if self.mostrar_ubicaciones:
            worksheet1.col(indextipomov).width = 8000
            worksheet1.col(indextipomov + 1).width = 8000
            indextipomov += 2
        if self.sd_notdocuments:
            indextipomov += 1
            worksheet1.col(2).width = 7000
        worksheet1.col(indextipomov).width = 15000

        #CODIGO PARA RECORRER LAS DEMAS COLUMNAS Y HACER ESPACIO PARA EL PRODUCTO
        indextipomov += 1
        worksheet1.col(indextipomov).width = 12000
        #FIN DEL CODIGO EXTRA


        for i in range(9):
            worksheet1.col(indextipomov + i).width = 3500
        # CODIGO ZONA HORARIA HENRY
        date_start_zone =  datetime.combine(self.date_start, time.min) +timedelta(hours=4) if self.date_start else self.date_start
        date_end_zone = datetime.combine(self.date_end, time.max) + timedelta(hours=4) if self.date_end else self.date_end
        # ZONA HORARIA HENRY END
        kardex_almacenes = self.datos_kardex(date_start_zone, date_end_zone, self.seleccionalmacenes, self.filtraralmacenes)

        indexrow = 4

        totalcolumns = 14
        if self.filtrartipomov: totalcolumns += 1
        if self.mostrar_ubicaciones: totalcolumns += 2
        if self.sd_notdocuments: totalcolumns += 1
        indextipomov = 3
        if self.filtrartipomov:
            indextipomov += 1
        if self.mostrar_ubicaciones:
            indextipomov += 2
        if self.sd_notdocuments:
            indextipomov += 1
        total_valor_global = 0
        total_cantidad_global = 0

        # RELLENAMOS CABECERA
        worksheet1.row(3).height = 500
        style_header = xlwt.easyxf(
            "font: name Calibri, height 200, color black, bold on; align: horiz left; borders: left thin, right thin")
        fecha_inicio = 'primer registro'
        fecha_fin = 'fecha actual'
        if self.date_start: fecha_inicio = str(date_start_zone)
        if self.date_end: fecha_fin = str(date_end_zone)
        worksheet1.write_merge(2, 2, 0, 1, 'Rango de fechas:', style_header)
        worksheet1.write(2, 2, 'Compañia:', style_header)
        almacen_categoria_col = 15
        if not self.filtrartipomov: almacen_categoria_col -= 1
        if not self.mostrar_ubicaciones: almacen_categoria_col -= 2
        if not self.sd_notdocuments: almacen_categoria_col -= 1
        worksheet1.write_merge(2, 2, 3, almacen_categoria_col - 6, 'Almacenes: ', style_header)
        worksheet1.write_merge(2, 2, almacen_categoria_col - 5, almacen_categoria_col, 'Categorias: ', style_header)

        lista_almacenes = ''
        todo_almacenes = []
        almacenes = self.seleccionalmacenes
        if not self.seleccionalmacenes:
            almacenes = self.env['stock.warehouse'].search([])
        i = 0
        for almacen in almacenes:
            i += 1
            todo_almacenes.append(almacen.name)
            if i == len(todo_almacenes):
                lista_almacenes += almacen.name
            else:
                lista_almacenes += almacen.name + ', '

        lista_categorias = ''
        todo_categorias = []

        for cat in self.categ_id:
            todo_categorias.append(cat.name)
        if len(todo_categorias) == 0:
            for Almacen in kardex_almacenes:
                for categoria in kardex_almacenes[Almacen]:
                    if categoria not in todo_categorias:
                        todo_categorias.append(categoria)
        i = 0
        for categoria in todo_categorias:
            i += 1
            if i == len(todo_categorias):
                lista_categorias += categoria
            else:
                lista_categorias += categoria + ', '

        worksheet1.write_merge(3, 3, 0, 1, fecha_inicio + " - " + fecha_fin, xlwt.easyxf(
            "font: name Calibri, height 200, color black; align: vert center,horiz left; borders: left thin, right thin"))
        worksheet1.write(3, 2, self.env.user.company_id.name, xlwt.easyxf(
            "font: name Calibri, height 200, color black; align: vert center, horiz left; borders: left thin, right thin"))
        worksheet1.write_merge(3, 3, 3, almacen_categoria_col - 6, lista_almacenes, xlwt.easyxf(
            "font: name Calibri, height 200, color black; align: vert center, horiz left; borders: left thin, right thin"))
        worksheet1.write_merge(3, 3, almacen_categoria_col - 5, almacen_categoria_col, lista_categorias, xlwt.easyxf(
            "font: name Calibri, height 200, color black; align: vert center, horiz left; borders: left thin, right thin"))

        # FOR PARA PONER MARGENES A LAS CASILLAS
        for margen_columna in range(totalcolumns):
            worksheet1.write(6, margen_columna, "",
                             xlwt.easyxf("borders: left thin, right thin, bottom thin, top thin"))

        # SUMAMOS INDEX PARA HACER ESPACIO PARA EL PRODUCTO (PARCHE :( )
        indextipomov += 1
        style_kardex = xlwt.easyxf("font: name Calibri, height 200, color black, bold on; align: horiz left; borders: left thin, right thin, bottom thin")  # ; pattern: pattern solid, fore_colour lavender
        worksheet1.write_merge(6, 6, 0, 2, "ALMACEN TOTAL", style_kardex)

        # print('TERMINO LA CABECERA!!')

        balance_anterior = []
        if self.date_start:
            balance_anterior = self.balance_previo(date_start_zone,date_end_zone, self.seleccionalmacenes, self.filtraralmacenes)
            # print('balance previo: ', len(balance_anterior))

        style_kardex_numeric = xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz right; borders: left thin, right thin, bottom thin")
        style_kardex_numeric_bold = xlwt.easyxf("font: name Calibri, height 200, color black, bold on; align: horiz right; borders: left thin, right thin, bottom thin")

        style_kardex_numeric.num_format_str = '#,##0.00'
        style_kardex_numeric_bold.num_format_str = '#,##0.00'

        productos_transf_intern = {}

        for last_almacen,almacen in enumerate(kardex_almacenes):
            #IMPRIMIR NOMBRE DEL ALMACEN Y SALTO DE LINEA SI SE FILTRAN ALMACENES
            Nro = 1
            total_valor_almacen = 0
            total_cantidad_almacen = 0
            index_total_almacen = indexrow + 3

            if self.filtraralmacenes:
                style_kardex = xlwt.easyxf("font: name Calibri, height 200, color black, bold on; align: horiz left; borders: left thin, right thin, bottom thin")  # ; pattern: pattern solid, fore_colour lavender
                # FOR PARA PONER MARGENES A LAS CASILLAS
                for margen_columna in range(totalcolumns):
                    worksheet1.write((3 + indexrow), margen_columna, "", xlwt.easyxf("borders: left thin, right thin, bottom thin, top thin"))
                worksheet1.write_merge((3 + indexrow), (3 + indexrow), 0, 2, str(self.name_ubicacion(almacen)).upper(), style_kardex)
                indexrow += 1
            for last_categoria,categoria in enumerate(kardex_almacenes[almacen]):
                # IMPRIMIR CATEGORIA Y SALTO DE LINEA SI SE FILTRAN CATEGORIAS
                total_valor_categoria = 0
                total_cantidad_categoria = 0
                index_total_categoria = indexrow + 3
                if self.filtrarcategorias:
                    # FOR PARA PONER MARGENES A LAS CASILLAS
                    for margen_columna in range(totalcolumns):
                        worksheet1.write((3 + indexrow), margen_columna, "", xlwt.easyxf("borders: left thin, right thin, bottom thin, top thin"))

                    style_kardex = xlwt.easyxf("font: name Calibri, height 200, color black, bold on; align: horiz left; borders: left thin, right thin, bottom thin") # ; pattern: pattern solid, fore_colour aqua
                    worksheet1.write_merge((3 + indexrow), (3 + indexrow), 0, 2, "              " + categoria.upper(), style_kardex)
                    indexrow += 1
                for last_producto,  producto in enumerate(kardex_almacenes[almacen][categoria]):
                    # FOR PARA PONER MARGENES A LAS CASILLAS
                    for margen_columna in range(totalcolumns):
                        worksheet1.write((3 + indexrow), margen_columna, "", xlwt.easyxf("borders: left thin, right thin, bottom thin, top thin"))

                    style_kardex = xlwt.easyxf("font: name Calibri, height 200, color black; align: horiz left; borders: left thin, right thin, bottom thin")

                    cantidadtotal = 0
                    totalproducto = 0
                    sumar_previo = True
                    list_cost_actualice = None
                    elemento_coste = []
                    for last_move, stock_move_id in enumerate(kardex_almacenes[almacen][categoria][producto]):
                            # adicionar cost_actualice en el excel - HENRY
                            # INICIO
                            if not list_cost_actualice:
                                list_cost_actualice = self.actualizacion_costo(stock_move_id['product_id'])
                            # print('elemento_coste',elemento_coste)
                            # print('list_cost_actualice',list_cost_actualice)
                            filtered_cost_actualice = [m for m in list_cost_actualice if m not in elemento_coste]

                            # Luego, itera sobre los elementos filtrados
                            for cost_actualice in filtered_cost_actualice:
                                if cost_actualice['date'] <=  stock_move_id['date']:
                                    if cantidadtotal != 0:
                                        worksheet1.write((3 + indexrow), 1, str(cost_actualice["date"]), style_kardex)
                                        worksheet1.write((3 + indexrow), 0, str(Nro), style_kardex)
                                        worksheet1.write((3 + indexrow), 2, stock_move_id["product_category"], style_kardex)
                                        codigo = ""
                                        if stock_move_id["default_code"]:
                                            codigo = stock_move_id["default_code"] + " "
                                        detalle_sum = 6 if self.sd_notdetails else 1
                                        worksheet1.write((3 + indexrow), detalle_sum  + 1 ,codigo + cost_actualice["product_name"], style_kardex)
                                        value_coste_actualiza = (cost_actualice['value_actual'] / cost_actualice['quantity_total']) * cantidadtotal
                                        totalproducto += value_coste_actualiza
                                        if self.sd_notdetails:
                                            if cost_actualice['value_actual'] > 0:
                                                worksheet1.write((3 + indexrow), detalle_sum + 4, abs(value_coste_actualiza),style_kardex_numeric)
                                            else:
                                                worksheet1.write((3 + indexrow), detalle_sum  + 7,abs(value_coste_actualiza), style_kardex_numeric)
                                            worksheet1.write((3 + indexrow), 2,'ACTUALZIACION DEL COSTE - MANUAL', style_kardex)
                                            worksheet1.write((3 + indexrow), detalle_sum + 8, cantidadtotal, style_kardex_numeric)
                                            worksheet1.write((3 + indexrow), detalle_sum + 10 , totalproducto,style_kardex_numeric)
                                            worksheet1.write((3 + indexrow), detalle_sum + 9,totalproducto / cantidadtotal,style_kardex_numeric)
                                            Nro += 1
                                            indexrow += 1
                                    elemento_coste.append(cost_actualice)
                                break
                            #     FIN COSTE ACTUALIZADO

                            # FOR PARA PONER MARGENES A LAS CASILLAS
                            for margen_columna in range(totalcolumns):
                                worksheet1.write((3 + indexrow), margen_columna, "", xlwt.easyxf("borders: left thin, right thin, bottom thin, top thin"))

                            cantidadexistencia = 0
                            valueexistencia = 0

                            if sumar_previo:
                                if almacen in balance_anterior:
                                    if categoria in balance_anterior[almacen]:
                                        if producto in balance_anterior[almacen][categoria]:
                                            sumar_previo = False
                                            cantidadtotal += balance_anterior[almacen][categoria][producto]["Cantidad"]
                                            totalproducto += balance_anterior[almacen][categoria][producto]["Valor_total"]
                                            balance_anterior[almacen][categoria][producto]["Valor_total"] = 0
                                            balance_anterior[almacen][categoria][producto]["Cantidad"] = 0
                                            # print('balance anterior rest: ', balance_anterior)

                            #PARA ESCRIBIR CODIGO - NOMBRE PRODUCTO EN CADA LINEA
                            codigo = ""
                            if stock_move_id["default_code"]:
                                codigo = stock_move_id["default_code"] + " "
                            worksheet1.write((3 + indexrow), indextipomov - 1, codigo + stock_move_id["product_name"], style_kardex)

                            worksheet1.write((3 + indexrow), 1, str(stock_move_id["date"]), style_kardex)
                            worksheet1.write((3 + indexrow), 0, str(Nro), style_kardex)
                            worksheet1.write((3 + indexrow), 2, stock_move_id["product_category"], style_kardex)
                            if self.filtrartipomov:
                                # CODIGO PARA RECORRER 2 ESPACIOS MENOS EN CASO QUE SE MUESTREN UBICACIONES
                                index_location = 1 if self.sd_notdocuments else 0
                                if self.mostrar_ubicaciones:
                                    index_location += 2
                                worksheet1.write((3 + indexrow), indextipomov - 2 - index_location, stock_move_id['type'], style_kardex)
                                #CODIGO PARA ADICIONAR DESECHO COMO CONCEPTO EXTRA
                                if stock_move_id['type'] == "Ajuste de inventario de salida" and stock_move_id["scrap_names"]:
                                    worksheet1.write((3 + indexrow), indextipomov - 2 - index_location, "Desecho", style_kardex)

                            if self.mostrar_ubicaciones:
                                destino_padre = ""
                                origen_padre = ""
                                ubicacion_origen_parent = stock_move_id["parent_sl_or_name"]
                                ubicacion_destino_parent = stock_move_id["parent_sl_dest_name"]
                                if ubicacion_destino_parent:
                                    destino_padre = ubicacion_destino_parent
                                if ubicacion_origen_parent:
                                    origen_padre = ubicacion_origen_parent
                                worksheet1.write((3 + indexrow), indextipomov - 3, destino_padre + "/" + stock_move_id["destine_name"], style_kardex)
                                worksheet1.write((3 + indexrow), indextipomov - 4, origen_padre + "/" + stock_move_id["origin_name"], style_kardex)
                            if stock_move_id['type'] in ["Compra", "Ajuste de Inventario Entrada", "Transferencia interna", "Produccion para almacen"]:
                                if self.sd_notdocuments:
                                    documento = ""
                                    if stock_move_id["picking_id"]:
                                        documento += str(stock_move_id["picking_name"]) + " - "
                                    if stock_move_id['type'] == "Compra":
                                        documento += str(stock_move_id["purchase_name"])
                                    if stock_move_id['type'] == "Ajuste de Inventario Entrada":
                                        documento += str(stock_move_id["inventory_name"])
                                    if stock_move_id['type'] == "Produccion para almacen":
                                        documento += str(stock_move_id["production_name"])
                                    if stock_move_id['type'] == "Transferencia interna":
                                        documento += str(stock_move_id["picking_name"])
                                    worksheet1.write((3 + indexrow), indextipomov -2, documento, style_kardex)
                                cantidadexistencia += abs(stock_move_id["svl_ids_quantity_sum"])
                                valueexistencia += abs(stock_move_id["svl_ids_value_sum"])
                                if cantidadexistencia == 0:
                                    cantidadexistencia += abs(stock_move_id["product_uom_qty"])
                                indextransfintern = 0
                                if valueexistencia == 0 and stock_move_id["type"] == 'Transferencia interna':
                                    valueexistencia = abs(self.return_value_promedio_transferencias_internas(stock_move_id["product_id"],stock_move_id['date'])) * cantidadexistencia
                                # CODIGO PARA COLUMNA PRECIO UNITARIO Y TOTAL EN TRANSFERENCIAS INTERNAS
                                if (stock_move_id['type'] == "Transferencia interna") and (almacen != stock_move_id["nombre_alm_dest"]):
                                    if stock_move_id["nombre_alm_or"] in todo_almacenes:
                                        indextransfintern += 3
                                if self.sd_notdetails:
                                    worksheet1.write((3 + indexrow), indextipomov + indextransfintern + 1, valueexistencia / cantidadexistencia, style_kardex_numeric)
                                    worksheet1.write((3 + indexrow), indextipomov + indextransfintern + 0, cantidadexistencia, style_kardex_numeric)
                                    worksheet1.write((3 + indexrow), indextipomov + indextransfintern + 2, valueexistencia, style_kardex_numeric)
                            else:
                                if self.sd_notdocuments:
                                    if stock_move_id['type'] == "Venta":
                                        documento = ""
                                        if stock_move_id["picking_id"]:
                                            documento += str(stock_move_id["picking_name"])
                                        if stock_move_id["sale_line_id"]:
                                            documento += " - " + str(stock_move_id["sale_name"])
                                        else:
                                            if stock_move_id["picking_id"]:
                                                documento += " - " + str(stock_move_id["picking_origin"])
                                        worksheet1.write((3 + indexrow), indextipomov-2, documento, style_kardex)
                                    if stock_move_id['type'] == "Ajuste de inventario de salida":
                                        worksheet1.write((3 + indexrow), indextipomov-2, str(stock_move_id["origin"]) + " - " + stock_move_id["documento"], style_kardex)
                                        if stock_move_id["scrap_names"]:
                                            for scrap in stock_move_id["scrap_names"]:
                                                worksheet1.write((3 + indexrow), indextipomov-2, str(stock_move_id["origin"]) + " - " + scrap, style_kardex)

                                    if stock_move_id['type'] == "Materia prima para produccion":
                                        worksheet1.write((3 + indexrow), indextipomov-2, stock_move_id["production_name"], style_kardex)
                                cantidadexistencia += abs(stock_move_id["svl_ids_quantity_sum"])
                                valueexistencia += abs(stock_move_id["svl_ids_value_sum"])

                                if cantidadexistencia == 0:
                                    cantidadexistencia += abs(stock_move_id["product_uom_qty"])
                                if self.sd_notdetails:
                                    worksheet1.write((3 + indexrow), indextipomov + 4, valueexistencia / cantidadexistencia, style_kardex_numeric)
                                    worksheet1.write((3 + indexrow), indextipomov + 3, cantidadexistencia, style_kardex_numeric)
                                    worksheet1.write((3 + indexrow), indextipomov + 5, valueexistencia, style_kardex_numeric)

                            # CODIGO PARA RELLENAR DICCIONARIO DE PRODUCTOS CON ACUMULADO DEL KARDEX (TRANSF. INTERNAS)

                            if stock_move_id['type'] not in ["Compra","Ajuste de Inventario Entrada","Transferencia interna", "Produccion para almacen"]:
                                # print('compra, ajuste, etc..')
                                cantidadtotal -= cantidadexistencia
                                totalproducto -= valueexistencia
                            else:
                                if (stock_move_id['type'] == "Transferencia interna") and (almacen != stock_move_id["nombre_alm_dest"]):
                                    # print('almacen destino',almacen ,'o',stock_move_id["nombre_alm_dest"] )
                                    if stock_move_id["nombre_alm_or"] in todo_almacenes:
                                        # print('alamcen origen',stock_move_id["nombre_alm_or"],' y  todo_almacenes')
                                        cantidadtotal -= cantidadexistencia
                                        totalproducto -= valueexistencia
                                    else:
                                        cantidadtotal += cantidadexistencia
                                        totalproducto += valueexistencia
                                else:

                                    cantidadtotal += cantidadexistencia
                                    totalproducto += valueexistencia


                            worksheet1.write((3 + indexrow), indextipomov + (6 if self.sd_notdetails else 0), cantidadtotal, style_kardex_numeric)
                            if cantidadtotal > 0:
                                worksheet1.write((3 + indexrow), indextipomov + (7 if self.sd_notdetails else 1), totalproducto / cantidadtotal, style_kardex_numeric)
                            else:
                                worksheet1.write((3 + indexrow), indextipomov + (7 if self.sd_notdetails else 1), 0, style_kardex_numeric)

                            worksheet1.write((3 + indexrow), indextipomov + (8 if self.sd_notdetails else 2), totalproducto, style_kardex_numeric)
                            if last_move == len(kardex_almacenes[almacen][categoria][producto]) - 1:
                                worksheet1.write((3 + indexrow), indextipomov + (6 if self.sd_notdetails else 0), cantidadtotal, style_kardex_numeric_bold)
                                if cantidadtotal > 0:
                                    worksheet1.write((3 + indexrow), indextipomov + (7 if self.sd_notdetails else 1), totalproducto / cantidadtotal,
                                                     style_kardex_numeric_bold)
                                else:
                                    worksheet1.write((3 + indexrow), indextipomov + (7 if self.sd_notdetails else 1), 0, style_kardex_numeric_bold)
                                worksheet1.write((3 + indexrow), indextipomov + (8  if self.sd_notdetails else 2), totalproducto, style_kardex_numeric_bold)
                            # indexrow += 1
                            if self.sd_notdetails:
                                indexrow += 1
                                Nro += 1
                            else:
                                if last_move == len(kardex_almacenes[almacen][categoria][producto]) - 1:
                                    if not self.filtraralmacenes and not self.filtrarcategorias:
                                        indexrow += 1
                                        Nro += 1
                                    #PARA NO IMPRIMIR LA ULTIMA LINEA
                                    if last_producto == len(kardex_almacenes[almacen][categoria]) - 1 and last_categoria == len(kardex_almacenes[almacen]) - 1 and last_almacen == len(kardex_almacenes) - 1:
                                        worksheet1.write((3 + indexrow),0, '')
                                        worksheet1.write((3 + indexrow), 1, '')
                                        worksheet1.write((3 + indexrow), 2, '')
                                        worksheet1.write((3 + indexrow), 3, '')
                                        worksheet1.write((3 + indexrow), 4, '')
                                        worksheet1.write((3 + indexrow), 5, '')
                                        worksheet1.write((3 + indexrow), 6, '')
                                        worksheet1.write((3 + indexrow), 7, '')
                                        worksheet1.write((3 + indexrow), 8, '')
                                        worksheet1.write((3 + indexrow), 9, '')
                                        worksheet1.write((3 + indexrow), 10, '')
                                        worksheet1.write((3 + indexrow), 11, '')
                                        worksheet1.write((3 + indexrow), 12, '')
                                        worksheet1.write((3 + indexrow), 13, '')
                                        worksheet1.write((3 + indexrow), 14, '')
                                        worksheet1.write((3 + indexrow), 15, '')
                                        worksheet1.write((3 + indexrow), 16, '')
                                        worksheet1.write((3 + indexrow), 17, '')
                    if cantidadtotal != 0:
                        total_valor_categoria += totalproducto
                        total_cantidad_categoria += cantidadtotal
                if total_cantidad_categoria != 0:
                    total_valor_almacen += total_valor_categoria
                    total_cantidad_almacen += total_cantidad_categoria
                if self.filtrarcategorias:
                    worksheet1.write(index_total_categoria, indextipomov + (8 if self.sd_notdetails else 2), total_valor_categoria, style_kardex_numeric_bold)
                    if total_cantidad_categoria > 0:
                        worksheet1.write(index_total_categoria, indextipomov + (7 if self.sd_notdetails else 1), total_valor_categoria/total_cantidad_categoria, style_kardex_numeric_bold)
                    else:
                        worksheet1.write(index_total_categoria, indextipomov + (7 if self.sd_notdetails else 1), 0, style_kardex_numeric_bold)
                    worksheet1.write(index_total_categoria, indextipomov + (6 if self.sd_notdetails else 0), total_cantidad_categoria, style_kardex_numeric_bold)
            if total_cantidad_almacen != 0:
                total_valor_global += total_valor_almacen
                total_cantidad_global += total_cantidad_almacen
            if self.filtraralmacenes:
                worksheet1.write(index_total_almacen, indextipomov + (8 if self.sd_notdetails else 2), total_valor_almacen, style_kardex_numeric_bold)
                if total_cantidad_almacen > 0:
                    worksheet1.write(index_total_almacen, indextipomov + (7 if self.sd_notdetails else 1), total_valor_almacen/total_cantidad_almacen, style_kardex_numeric_bold)
                else:
                    worksheet1.write(index_total_almacen, indextipomov + (7 if self.sd_notdetails else 1), 0, style_kardex_numeric_bold)
                worksheet1.write(index_total_almacen, indextipomov + (6 if self.sd_notdetails else 0), total_cantidad_almacen, style_kardex_numeric_bold)

            if not self.filtraralmacenes:
                indexrow += 1
        worksheet1.write(6, indextipomov + (8 if self.sd_notdetails else 2), total_valor_global, style_kardex_numeric_bold)
        if total_cantidad_global > 0:
            worksheet1.write(6, indextipomov +  (7 if self.sd_notdetails else 1), total_valor_global/total_cantidad_global, style_kardex_numeric_bold)
        else:
            worksheet1.write(6, indextipomov + (7 if self.sd_notdetails else 1), 0, style_kardex_numeric_bold)
        worksheet1.write(6, indextipomov + (6 if self.sd_notdetails else 0), total_cantidad_global, style_kardex_numeric_bold)

        # GUARDAR REPORTE EXCEL-------------------------------------------------------------
        fp = io.BytesIO()
        reporte.save(fp)
        self.write({'excel_file': base64.encodestring(fp.getvalue()), 'file_name': 'Reporte Kardex.xls'})
        res = {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'kardex.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res


    def balance_previo(self, date_start, date_end, lista_almacenes, filtro_almacenes):
        consulta_categoria = self.get_productos()
        # stock_move_ids = self.env['stock.move'].search([('state', '=', 'done'),('date', '<', date_start),consulta_categoria],order='date asc')

        date_conditions = self.construct_date_conditions(date_start)
        query = """
                                SELECT sm.date,
                                    sm.id AS stock_move_id, 
                                    sm.reference AS documento,
                                    sm.purchase_line_id,
                                    sm.sale_line_id,
                                    sm.inventory_id,
                                    sm.picking_id,
                                    sp.name AS picking_name,
                                    sp.origin AS picking_origin,
                                    sm.production_id,
                                    sm.origin,
                                    sm.product_uom_qty,
                                    pt.name AS product_name,
                                    pt.id AS product_id,
                                    pt.list_price,
                                    pt.default_code,
                                    pc.name AS product_category,
                                    sm.location_id,
                                    sm.location_dest_id,
                                    sl_or.usage AS origin_usage,
                                    sl_or.name AS origin_name,
                                    sl_dest.usage AS destine_usage,
                                    sl_dest.name AS destine_name,
                                    sl_or_parent.name AS parent_sl_or_name,
                                    sl_dest_parent.name AS parent_sl_dest_name,
                                    sm.sd_almacen_origen AS almacen_origen,
                                    sm.sd_almacen_destino AS almacen_destino,
                                    sw_or.name AS nombre_alm_or,
                                    sw_dest.name AS nombre_alm_dest,
                                    svl.quantity,
                                    svl.unit_cost,
                                    po.name AS purchase_name,
                                    si.name AS inventory_name,
                                    so.name AS sale_name,
                                    prod.name AS production_name,
                                    (
                                        SELECT COALESCE(SUM(value), 0)
                                        FROM stock_valuation_layer svl_sub
                                        WHERE svl_sub.stock_move_id = sm.id
                                    ) AS svl_ids_value_sum,
                                    (
                                        SELECT COALESCE(SUM(quantity), 0)
                                        FROM stock_valuation_layer svl_sub
                                        WHERE svl_sub.stock_move_id = sm.id
                                    ) AS svl_ids_quantity_sum,
                                    (
                                        SELECT name
                                        FROM stock_scrap st_sc
                                        WHERE st_sc.move_id = sm.id
                                    ) AS scrap_names
                                FROM stock_move sm
                                JOIN (
                                    SELECT DISTINCT ON (move_id) move_id, id
                                    FROM stock_move_line
                                ) sml ON sm.id = sml.move_id
                                JOIN product_product pp ON sm.product_id = pp.id  -- Corregido aquí
                                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                JOIN stock_location sl_or ON sm.location_id = sl_or.id
                                JOIN stock_location sl_dest ON sm.location_dest_id = sl_dest.id
                                JOIN product_category pc ON pt.categ_id = pc.id
                                LEFT JOIN stock_warehouse sw_or ON sm.sd_almacen_origen = sw_or.id
                                LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
                                LEFT JOIN purchase_order_line pol ON sm.purchase_line_id = pol.id
                                LEFT JOIN purchase_order po ON pol.order_id = po.id
                                LEFT JOIN sale_order_line sol ON sm.sale_line_id = sol.id
                                LEFT JOIN sale_order so ON sol.order_id = so.id
                                LEFT JOIN stock_location sl_or_parent ON sl_or.location_id = sl_or_parent.id
                                LEFT JOIN stock_location sl_dest_parent ON sl_dest.location_id = sl_dest_parent.id
                                LEFT JOIN stock_warehouse sw_dest ON sm.sd_almacen_destino = sw_dest.id
                                LEFT JOIN stock_inventory si ON sm.inventory_id = si.id
                                LEFT JOIN mrp_production prod ON sm.production_id = prod.id
                                LEFT JOIN stock_valuation_layer svl ON sm.id = svl.stock_move_id
                                WHERE sm.state = 'done' {consulta_fecha} {consulta_categoria}
                                ORDER BY date ASC

                            """.format(consulta_fecha=date_conditions, consulta_categoria=consulta_categoria)
        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()
        # print('result reporte previo : ', len(results))

        # print('stock move ids: ', stock_move_ids)
        kardex_almacenes = {}
        seleccionalmacenes = []
        almacenes = lista_almacenes
        if len(almacenes) == 0:
            almacenes = self.env['stock.warehouse'].search([])
        for almacen in almacenes:
            seleccionalmacenes.append(almacen.display_name)
        array_product_ids = []
        for product in self.seleccionproductos:
            array_product_ids.append(product.id)

    # AGRUPAR MOVIMIENTO DE EXISTENCIAS POR ALMACEN/CATEGORIA/PRODUCTO/TIPO DE MOVIMIENTO
        for stock_move_id in results:
            print('stock_move_id',stock_move_id)
            lista_almacenes = ['kardex global']
            location_id = stock_move_id["origin_usage"]
            location_dest_id = stock_move_id["destine_usage"]
            switcher = {
                'supplier_internal': 'Compra',
                'transit_internal': 'Compra',
                'internal_customer': 'Venta',
                'internal_transit': 'Venta',
                'internal_inventory': 'Ajuste de inventario de salida',
                'internal_internal': 'Transferencia interna',
                'inventory_internal': 'Ajuste de Inventario Entrada',
                'production_internal': 'Produccion para almacen',
                'internal_production': 'Materia prima para produccion'
            }
            tipo = switcher.get(location_id + '_' + location_dest_id, 'No definido')
            # mov_stock = self.env['stock.move'].search([('id', '=', stock_move_id["stock_move_id"])])
            almacen_origen = stock_move_id['nombre_alm_or']
            almacen_destino = stock_move_id['nombre_alm_dest']

            cantidad = 0
            valor_asiento = 0
            if tipo == 'Transferencia interna' and (almacen_origen in seleccionalmacenes and almacen_destino in seleccionalmacenes) and not filtro_almacenes:
                continue

            if tipo in ['Venta', 'Ajuste de inventario de salida', 'Materia prima para produccion', 'Produccion para almacen']:
                cantidad -= abs(stock_move_id["svl_ids_quantity_sum"])
                if cantidad == 0:
                    cantidad -= abs(stock_move_id["product_uom_qty"])
                valor_asiento -= abs(stock_move_id["svl_ids_value_sum"])
                if valor_asiento == 0 and tipo == 'Transferencia interna':
                    valor_asiento -= self.return_value_promedio_transferencias_internas(stock_move_id["product_id"],stock_move_id['date'])
            if tipo in ['Compra', 'Ajuste de Inventario Entrada']:
                cantidad += abs(stock_move_id["svl_ids_quantity_sum"])
                if cantidad == 0:
                    cantidad += abs(stock_move_id["product_uom_qty"])
                valor_asiento += abs(stock_move_id["svl_ids_value_sum"])

            # CONDICION PARA FILTRAR POR ALMACEN
            if almacen_origen in seleccionalmacenes or almacen_destino in seleccionalmacenes:
                # CONDICION PARA FILTRAR POR PRODUCTO
                if (len(self.seleccionproductos) == 0) or stock_move_id["product_id"] in array_product_ids:
                    # print("cant - val: ", cantidad, ' ', valor_asiento)
                    if filtro_almacenes:
                        switcher = {
                            'Compra': [almacen_destino],
                            'Venta': [almacen_origen],
                            'Transferencia interna': [almacen_origen, almacen_destino],
                            'Ajuste de inventario de salida': [almacen_origen],
                            'Ajuste de Inventario Entrada': [almacen_destino],
                            'Produccion para almacen': [almacen_destino],
                            'Materia prima para produccion': [almacen_origen]
                        }
                        lista_almacenes = switcher.get(tipo, [almacen_origen])
                    # else:
                    #     if tipo == 'Transferencia interna' and almacen_origen in seleccionalmacenes and almacen_destino in seleccionalmacenes:
                    #         continue
                    #     almacen_origen = 'kardex global'

                    # if (almacen_origen != almacen_destino):
                    for almacen_actual in lista_almacenes:
                        if tipo == 'Transferencia interna':
                            cantidad = 0
                            valor_asiento = 0
                            if almacen_actual == almacen_origen:
                                cantidad -= abs(stock_move_id["product_uom_qty"])
                                valor_asiento -= self.return_value_promedio_transferencias_internas(stock_move_id["product_id"],stock_move_id['date'])
                            else:
                                cantidad += abs(stock_move_id["product_uom_qty"])
                                valor_asiento += self.return_value_promedio_transferencias_internas(stock_move_id["product_id"],stock_move_id['date'])
                        nuevo = True
                        # print('tipo: ', tipo, ' - cantidad: ', cantidad, ' - valor asiento: ', valor_asiento)
                        # if not (tipo == "Transferencia interna" and (not self.filtraralmacenes or almacen_origen == almacen_destino)):
                        if (almacen_actual in kardex_almacenes and (almacen_actual in seleccionalmacenes or 'kardex global' in lista_almacenes)):
                            if stock_move_id["product_category"] in kardex_almacenes[almacen_actual]:
                                if (stock_move_id["product_name"] in kardex_almacenes[almacen_actual][stock_move_id["product_category"]]) or ((not self.sinvariantes) and (stock_move_id["product_name"] in kardex_almacenes[almacen_actual][stock_move_id["product_category"]])):
                                    kardex_almacenes[almacen_actual][stock_move_id["product_category"]][stock_move_id["product_name"]]["Cantidad"] += cantidad
                                    kardex_almacenes[almacen_actual][stock_move_id["product_category"]][stock_move_id["product_name"]]["Valor_total"] += valor_asiento
                                    nuevo = False
                                    continue

                                if nuevo:
                                    kardex_almacenes[almacen_actual][stock_move_id["product_category"]][stock_move_id["product_name"]] = {"Cantidad": cantidad, "Valor_total": valor_asiento}
                                    # kardex_almacenes[index_kardex]["Almacen_Catgs"][index_almacen]["Catg_Products"].append({"Product": stock_move_id["product_name"], "Cantidad": cantidad, "Valor_total": valor_asiento})
                                    nuevo = False
                                    continue

                            if nuevo:
                                kardex_almacenes[almacen_actual][stock_move_id["product_category"]] = {
                                    stock_move_id["product_name"]: {"Cantidad": cantidad,
                                                                    "Valor_total": valor_asiento}}
                                nuevo = False
                                continue

                        if nuevo and (almacen_actual in seleccionalmacenes or almacen_actual == 'kardex global'):
                            if not filtro_almacenes:
                                kardex_almacenes['kardex global'] = {stock_move_id["product_category"]: {
                                    stock_move_id["product_name"]: {"Cantidad": cantidad,
                                                                    "Valor_total": valor_asiento}}}
                            else:
                                kardex_almacenes[almacen_actual] = {stock_move_id["product_category"]: {
                                    stock_move_id["product_name"]: {"Cantidad": cantidad, "Valor_total": valor_asiento}}}


        return kardex_almacenes


    def datos_kardex(self, date_start, date_end, lista_almacenes, filtro_almacenes):
        date_conditions = self.construct_date_conditions_ini_end(date_start, date_end)
        consulta_categoria = self.get_productos()
        query = """
                        SELECT sm.date,
                            sm.id AS stock_move_id, 
                            sm.reference AS documento,
                            sm.purchase_line_id,
                            sm.sale_line_id,
                            sm.inventory_id,
                            sm.picking_id,
                            sp.name AS picking_name,
                            sp.origin AS picking_origin,
                            sm.production_id,
                            sm.origin,
                            sm.product_uom_qty,
                            pt.name AS product_name,
                            pt.id AS product_id,
                            pt.list_price,
                            pt.default_code,
                            pc.name AS product_category,
                            sm.location_id,
                            sm.location_dest_id,
                            sl_or.usage AS origin_usage,
                            sl_or.name AS origin_name,
                            sl_dest.usage AS destine_usage,
                            sl_dest.name AS destine_name,
                            sl_or_parent.name AS parent_sl_or_name,
                            sl_dest_parent.name AS parent_sl_dest_name,
                            sm.sd_almacen_origen AS almacen_origen,
                            sm.sd_almacen_destino AS almacen_destino,
                            sw_or.name AS nombre_alm_or,
                            sw_dest.name AS nombre_alm_dest,
                            svl.quantity,
                            svl.unit_cost,
                            po.name AS purchase_name,
                            si.name AS inventory_name,
                            so.name AS sale_name,
                            prod.name AS production_name,
                            (
                                SELECT COALESCE(SUM(value), 0)
                                FROM stock_valuation_layer svl_sub
                                WHERE svl_sub.stock_move_id = sm.id
                            ) AS svl_ids_value_sum,
                            (
                                SELECT COALESCE(SUM(quantity), 0)
                                FROM stock_valuation_layer svl_sub
                                WHERE svl_sub.stock_move_id = sm.id
                            ) AS svl_ids_quantity_sum,
                            (
                                SELECT name
                                FROM stock_scrap st_sc
                                WHERE st_sc.move_id = sm.id
                            ) AS scrap_names
                        FROM stock_move sm
                        JOIN (
                            SELECT DISTINCT ON (move_id) move_id, id
                            FROM stock_move_line
                        ) sml ON sm.id = sml.move_id
                        JOIN product_product pp ON sm.product_id = pp.id  -- Corregido aquí
                        JOIN product_template pt ON pp.product_tmpl_id = pt.id
                        JOIN stock_location sl_or ON sm.location_id = sl_or.id
                        JOIN stock_location sl_dest ON sm.location_dest_id = sl_dest.id
                        JOIN product_category pc ON pt.categ_id = pc.id
                        LEFT JOIN stock_warehouse sw_or ON sm.sd_almacen_origen = sw_or.id
                        LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
                        LEFT JOIN purchase_order_line pol ON sm.purchase_line_id = pol.id
                        LEFT JOIN purchase_order po ON pol.order_id = po.id
                        LEFT JOIN sale_order_line sol ON sm.sale_line_id = sol.id
                        LEFT JOIN sale_order so ON sol.order_id = so.id
                        LEFT JOIN stock_location sl_or_parent ON sl_or.location_id = sl_or_parent.id
                        LEFT JOIN stock_location sl_dest_parent ON sl_dest.location_id = sl_dest_parent.id
                        LEFT JOIN stock_warehouse sw_dest ON sm.sd_almacen_destino = sw_dest.id
                        LEFT JOIN stock_inventory si ON sm.inventory_id = si.id
                        LEFT JOIN mrp_production prod ON sm.production_id = prod.id
                        LEFT JOIN stock_valuation_layer svl ON sm.id = svl.stock_move_id
                        WHERE sm.state = 'done' {consulta_fecha} {consulta_categoria}
                        ORDER BY date ASC

                    """.format(consulta_fecha=date_conditions, consulta_categoria=consulta_categoria)

        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()

        array_almacenes = ['kardex global']
        if lista_almacenes:
            array_almacenes = []
            for almacen in self.seleccionalmacenes:
                array_almacenes.append(almacen.display_name)
        if len(lista_almacenes) == 0 and filtro_almacenes:
            lista_almacenes = self.env['stock.warehouse'].search([])
            array_almacenes = []
            for almacen in lista_almacenes:
                array_almacenes.append(almacen.display_name)

        kardex_almacenes = {}

        for stock_move_id in results:
            # print('stock_move_id',stock_move_id)
            lista_almacenes_actual = ['kardex global']
            location_id = stock_move_id["origin_usage"]
            location_dest_id = stock_move_id["destine_usage"]
            almacen_origen = stock_move_id['nombre_alm_or']
            almacen_destino = stock_move_id['nombre_alm_dest']
            switcher = {
                'supplier_internal': 'Compra',
                'transit_internal': 'Compra',
                'internal_customer': 'Venta',
                'internal_transit': 'Venta',
                'internal_inventory': 'Ajuste de inventario de salida',
                'internal_internal': 'Transferencia interna',
                'inventory_internal': 'Ajuste de Inventario Entrada',
                'production_internal': 'Produccion para almacen',
                'internal_production': 'Materia prima para produccion',

            }
            tipo = switcher.get(str(location_id) + '_' + str(location_dest_id), 'No definido')
            stock_move_id['type'] = tipo

            if filtro_almacenes:
                switcher = {
                    'Compra': [almacen_destino],
                    'Venta': [almacen_origen],
                    'Transferencia interna': [almacen_origen, almacen_destino],
                    'Ajuste de inventario de salida': [almacen_origen],
                    'Ajuste de Inventario Entrada': [almacen_destino],
                    'Produccion para almacen': [almacen_destino],
                    'Materia prima para produccion': [almacen_origen]
                }
                lista_almacenes_actual = switcher.get(tipo, [almacen_origen])
            else:
                if tipo == 'Transferencia interna' and ((almacen_origen in array_almacenes and almacen_destino in array_almacenes) or array_almacenes == ['kardex global']):
                    continue
                almacen_origen = 'kardex global'
                almacen_destino = 'kardex global'

            if almacen_origen in array_almacenes or almacen_destino in array_almacenes or (not filtro_almacenes and (stock_move_id['nombre_alm_dest'] in array_almacenes or stock_move_id['nombre_alm_or'] in array_almacenes)):
                # print('lista_almacenes_actual', lista_almacenes_actual)
                for almacen_actual in lista_almacenes_actual:
                    if tipo == 'Transferencia interna' and almacen_actual not in array_almacenes and filtro_almacenes:
                        continue
                    if tipo == 'Transferencia interna' and not filtro_almacenes and stock_move_id["nombre_alm_or"] in array_almacenes and stock_move_id["nombre_alm_dest"] in array_almacenes:
                        continue
                    if almacen_actual not in array_almacenes:
                        if tipo in ['Compra', 'Ajuste de Inventario Entrada'] and stock_move_id['nombre_alm_dest'] not in array_almacenes:
                            continue
                        if tipo in ['Venta', 'Ajuste de inventario de salida', 'Produccion para almacen', 'Materia prima para produccion'] and stock_move_id['nombre_alm_or'] not in array_almacenes:
                            continue
                    if almacen_actual in kardex_almacenes:
                        if stock_move_id["product_category"] in kardex_almacenes[almacen_actual]:
                            if stock_move_id["product_name"] in kardex_almacenes[almacen_actual][stock_move_id["product_category"]]:
                                # print('dict', kardex_almacenes[almacen_actual][stock_move_id["product_category"]])
                                kardex_almacenes[almacen_actual][stock_move_id["product_category"]][stock_move_id["product_name"]].append(stock_move_id)
                                continue
                            kardex_almacenes[almacen_actual][stock_move_id["product_category"]][stock_move_id["product_name"]] = [stock_move_id]
                            continue
                        kardex_almacenes[almacen_actual][stock_move_id["product_category"]] = {stock_move_id["product_name"]:  [stock_move_id]}
                        continue

                    kardex_almacenes[almacen_actual] = {stock_move_id["product_category"]: {stock_move_id["product_name"]: [stock_move_id]}}

        # for almacen in kardex_almacenes:
        #     print('almacen: ', almacen)
        #     for categoria in kardex_almacenes[almacen]:
        #         print('---categoria: ', categoria)
        #         for producto in kardex_almacenes[almacen][categoria]:
        #             print('------producto: ', producto)
        #             for tipo in kardex_almacenes[almacen][categoria][producto]:
        #                 print('---------tipo: ', tipo)
        # print('kardex_almacenes: ', kardex_almacenes)
        # print('termino datos kardex')
        return kardex_almacenes
    def construct_date_conditions_ini_end(self, date_start, date_end):
        conditions = []

        if date_start:
            conditions.append(f"sm.date >= '{date_start}'")

        if date_end:
            conditions.append(f"sm.date <= '{date_end}'")

        if conditions:
            return "AND " + " AND ".join(conditions)
        else:
            return ""
    def construct_date_conditions(self, date_start):
        if date_start:
            return "AND "+ f"sm.date < '{date_start}'"
        else:
            return ""
    def identify_category_sons(self,categorias, cat_son_ids=None):
        cat_son_ids = []
        for cate in categorias:
            if cate not in cat_son_ids:
                cat_son_ids = cat_son_ids + [cat_hija for cat_hija in cate.child_id] #(1,2,3,4)[1,2,3,4]
                cat_id = self.identify_category_sons(cat_son_ids)
                cat_son_ids += cat_id
        return cat_son_ids

    def get_categorias(self):
        categoria = ('product_id', '!=', None)
        if self.categ_id:
            hijos = self.identify_category_sons(self.categ_id)
            for padre in self.categ_id:
                if padre not in hijos:
                    hijos.append(padre)
            categoria = ('product_id.categ_id', 'in', [hijo.id for hijo in hijos] )  # (1,3,6,78)
            #print('hijos: ', hijos, len(hijos))
        return categoria

    def get_productos(self):
        conditions_sm = ""
        conditions_svl = ""
        array_productos = []

        if self.seleccionproductos:
            for producto in self.seleccionproductos:
                if producto.id not in array_productos:
                    array_productos.append(producto.id)
        elif self.categ_id:
            hijos = self.identify_category_sons(self.categ_id)
            for padre in self.categ_id:
                if padre not in hijos:
                    hijos.append(padre)
            for hijo in hijos:
                productos_en_categoria = self.env['product.template'].search([('categ_id', '=', hijo.id)])
                for producto in productos_en_categoria:
                    if producto.id not in array_productos:
                        array_productos.append(producto.id)

        if array_productos:
            conditions_sm = "AND sm.product_id = ANY(ARRAY{array_productos})".format(array_productos=array_productos)

        return conditions_sm

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
    def return_value_promedio_transferencias_internas(self, product_id, date):
        # hacer una consulta en sql que consulte la tabla stock_valuation_layer y calcule el total de su atributo o campo value y quantity una vez esto retorne un resultado
        # entre la divicion de value / quantity, mucho cuidado con 0/0 ya que dara un error
        # condicion que el registro que se evaluara tiene que ser product_id == product_id y create_date == date, esta consulta debe recibir estos dos parametros
        # product_id, date
        query = """
           WITH avg_value AS (
                    SELECT 
                        CASE
                            WHEN COALESCE(SUM(quantity), 0) = 0 THEN 0
                            ELSE SUM(value) / SUM(quantity)
                        END AS average_value
                    FROM 
                        stock_valuation_layer
                    WHERE 
                        product_id = %s AND create_date <= %s
                ),
                last_positive_value AS (
                    SELECT 
                        value / quantity AS last_avg_value
                    FROM 
                        stock_valuation_layer
                    WHERE 
                        product_id = %s AND quantity > 0 AND create_date <= %s
                    ORDER BY 
                        create_date DESC
                    LIMIT 1
                )
                SELECT 
                    CASE
                        WHEN avg_value.average_value = 0 THEN COALESCE(last_positive_value.last_avg_value, 0)
                        ELSE avg_value.average_value
                    END AS final_value
                FROM 
                    avg_value
                LEFT JOIN 
                    last_positive_value ON avg_value.average_value = 0;
        """
        self.env.cr.execute(query, (product_id, date, product_id, date))
        value_promedio = self.env.cr.dictfetchall()
        if value_promedio:
            # print('value_promedio',value_promedio)
            return value_promedio[0]['final_value']
        else:
            return 0

    def name_ubicacion(self, nombre_almacen):
        stock_warehouse = self.env['stock.warehouse'].search([('name', '=', nombre_almacen)], limit=1)
        nombre_ubicacion_existencia = stock_warehouse.lot_stock_id.display_name if stock_warehouse else None
        return nombre_ubicacion_existencia

    import psycopg2
    from datetime import datetime

    def actualizacion_costo(self, product_id):
        if not product_id:
            return {}

        # Realizar la consulta SQL
        query = """
            SELECT
                pt.name AS product_name,
                svl.create_date AS date,
                svl.value AS value_actual,
                (
                    SELECT COALESCE(SUM(svl_sub.quantity), 0)
                    FROM stock_valuation_layer svl_sub
                    WHERE svl_sub.create_date < svl.create_date
                      AND svl_sub.product_id = svl.product_id
                      AND svl_sub.stock_move_id IS NOT NULL
                ) AS quantity_total
            FROM stock_valuation_layer svl
            JOIN product_product pp ON svl.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            WHERE svl.quantity = 0
              AND svl.stock_move_id IS NULL
              AND svl.product_id = %s
            ORDER BY svl.create_date
        """

        params = (product_id,)

        # Ejecutar la consulta
        self._cr.execute(query, params)
        result = self._cr.fetchall()

        # Convertir el resultado a un diccionario
        columns = ['product_name', 'date', 'value_actual', 'quantity_total']
        result_dict = [dict(zip(columns, row)) for row in result]

        return result_dict

