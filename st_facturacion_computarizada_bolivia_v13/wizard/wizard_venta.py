import json
import base64
import datetime
import os
import io
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class FacturaVentaReporte(models.TransientModel):
    _name = "factura.venta.reporte"
    _description = "Historial de las factura tipo venta"

    fecha_inicio = fields.Date(string='Fecha de inicio')
    fecha_final = fields.Date(string ='Fecha final')
    diario_venta = fields.Many2many('account.journal', required=True, string='Diario',domain="[('type','=','sale')]")

    def export_xls(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'diario': self.diario_venta.ids,
            'fecha_inicio': self.fecha_inicio,
            'fecha_final': self.fecha_final,

        }
        return {
            'type': 'ir_actions_xlsx_download_libro',
            'data': {'model': 'factura.venta.reporte',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Libro de Ventas',
                     }
        }
    def get_diario_Factura(self, data):
        wh = data.diario_venta.mapped('id')
        obj = self.env['account.move'].search([('journal_id', 'in', wh) or ('type','=','out_invoice')])
        # filtrar estado publicaco y anulado
        obj2 = self.filtro_estado(obj)
        obj3= self.ordenar_por_diario_y_menor_a_mayor(obj2,wh)
        # por hacer filtro de codigo de control si es factura computarizada
        nuevo_obejto_factura=[]
        for i in self.filtrar_por_fecha(obj3,data):
            vals={
                'numero_factura': i.fcb_numero_factura_computarizada or self.get_numero_factura(i.name),
                'fecha_factura': i.invoice_date.strftime("%d/%m/%Y"),
                'N_de_autorizacion': i.journal_id.fcb_numero_autorizacion_diario,
                'estado': 'V' if i.state == 'posted' else 'A',
                'NIT':( i.fcb_nit_a_facturar or i.partner_id.vat )if i.state == 'posted' else 0,
                'razon_social': (i.fcb_nombre_a_facturar or i.partner_id.name) if i.state == 'posted' else 'ANULADA',
                'importe_total': i.amount_total if i.state == 'posted' else 0,
                # advertencia si realiza una modificacion realice la operaciones correspondientes
                'importe_ice': 0,
                'exportaciones_operaciones_exentas': 0,
                'ventas_agravadas_a_tasa_cero': 0,
                # subtotal = importe_total-importe ice - exportaciones y operaciones exentas -ventas agravadas a tasa cero
                'subtotal': i.amount_total if i.state == 'posted' else 0,
                'descuentos': 0,
                #importe_base_para_debito_fiscal = subtotal - descuento , como no existe descuento realizamos el siguiente codigo
                'importe_base_para_debito_fiscal': round(i.amount_total if i.state == 'posted' else 0,2),
                #debito fiscal = importe_base_para_debito_fiscal *13%
                'debito_fiscal': round((i.amount_total*13)/100 if i.state == 'posted' else 0,2),
                'codigo_de_control': self.cambiar_o_por_0_codigo_control(i)
            }
            nuevo_obejto_factura.append(vals)
        return nuevo_obejto_factura

    def ordenar_por_diario_y_menor_a_mayor(self,facturas,diario_id):
        nuevo_objeto_acomodado = []
        cantidad_factura_diario = {}
        #acomodar por diario
        for i in diario_id:
            cantidad = 0
            for j in facturas:
                if j.journal_id.id == i:
                    cantidad += 1
                    nuevo_objeto_acomodado.append(j)
            cantidad_factura_diario[i] = cantidad
        # acomodar por numero de la factura de menor a mayor
        contador = 0
        for i in diario_id:
            for recorrido in range(1, cantidad_factura_diario[i]):
                for posicion in range(contador,cantidad_factura_diario[i] + contador-recorrido):
                    primero= nuevo_objeto_acomodado[posicion]
                    segundo = nuevo_objeto_acomodado[posicion+1]
                    if self.get_numero_factura(primero.name) > self.get_numero_factura(segundo.name):
                        temp= nuevo_objeto_acomodado[posicion]
                        nuevo_objeto_acomodado[posicion] = nuevo_objeto_acomodado[posicion+1]
                        nuevo_objeto_acomodado[posicion+1] = temp
            contador += cantidad_factura_diario[i]
        return nuevo_objeto_acomodado

    def cambiar_o_por_0_codigo_control(self,factura):
        nuevo_codigo_control = ''
        if factura.fcb_codigo_de_control:
            for caracter in factura.fcb_codigo_de_control:
                if caracter == 'O':
                    nuevo_codigo_control = nuevo_codigo_control+'0'
                else:
                    nuevo_codigo_control = nuevo_codigo_control+caracter
            return nuevo_codigo_control
        else:
            return factura.fcb_codigo_de_control

    def filtro_estado(self,objetos_facturas):
        diccionario = {'posted','cancel'}
        nuevo_objeto_factura = []
        for factura in objetos_facturas:
            if factura.state in diccionario:
                nuevo_objeto_factura.append(factura)
        return nuevo_objeto_factura

    def filtrar_por_fecha(self, objeto_Factura,data):
        nuevo_obejto_filtrado=[]
        if data.fecha_inicio or data.fecha_final:
            if data.fecha_inicio and data.fecha_final:
                #ambos existen
                if data.fecha_inicio <= data.fecha_final:
                    for factura in objeto_Factura:
                        if data.fecha_inicio <= factura.invoice_date <= data.fecha_final:
                            nuevo_obejto_filtrado.append(factura)
                else:
                    raise UserError('La fecha de finalización debe ser mayor que la fecha de inicio.')
            elif data.fecha_inicio:
                #fecha inicio existe
                for factura in objeto_Factura:
                    if data.fecha_inicio <= factura.invoice_date:
                        nuevo_obejto_filtrado.append(factura)
            else:
                #fecha final existe
                for factura in objeto_Factura:
                    if factura.invoice_date <= data.fecha_final:
                        nuevo_obejto_filtrado.append(factura)
        else:
            # no existe ninguno de los dos
            nuevo_obejto_filtrado = objeto_Factura
        return nuevo_obejto_filtrado

    def get_numero_factura(self, nombre):
        contador_slash = 0
        for letra in nombre:
            if '/' == letra:
                contador_slash += 1
        contador_slash_dos = 0
        concatenar_numero_secuencia = ''
        contar_cadenacion = 0
        for caracter in nombre:
            if contador_slash_dos == contador_slash:
                if contar_cadenacion <= 4:
                    concatenar_numero_secuencia = concatenar_numero_secuencia + caracter
                else:
                    break
            elif '/' == caracter:
                contador_slash_dos += 1
        return concatenar_numero_secuencia

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        lines = self.browse(data['ids'])
        get_diario_Factura = self.get_diario_Factura(lines)
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('libro de venta')
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px'})
        sheet.write(0, 0, 'ESPECIFICACIÓN', cell_format)
        sheet.write(0, 1,  'Nº', cell_format)
        sheet.write(0, 2, 'FECHA DE LA FACTURA', cell_format)
        sheet.write(0, 3, 'Nº DE LA FACTURA', cell_format)
        sheet.write(0, 4, 'Nº DE AUTORIZACIÓN', cell_format)
        sheet.write(0, 5, 'ESTADO', cell_format)
        sheet.write(0, 6, 'NIT/CI CLIENTE', cell_format)
        sheet.write(0, 7, 'NOMBRE O RAZON SOCIAL', cell_format)
        sheet.write(0, 8, 'IMPORTE TOTAL DE LA VENTA', cell_format)
        sheet.write(0, 9, 'IMPORTE ICE/IEHD/TASAS', cell_format)
        sheet.write(0, 10, 'EXPORTACIONES Y OPERACIONES EXENTAS', cell_format)
        sheet.write(0, 11, 'VENTAS GRAVADAS A TASA CERO', cell_format)
        sheet.write(0, 12, 'SUBTOTAL', cell_format)
        sheet.write(0, 13, 'DESCUENTOS, BONIFICACIONES Y REBAJAS OTORGADAS', cell_format)
        sheet.write(0, 14, 'IMPORTE BASE PARA DÉBITO FISCAL', cell_format)
        sheet.write(0, 15, 'DÉBITO FISCAL', cell_format)
        sheet.write(0, 16, 'CÓDIGO DE CONTROL', cell_format)

        #colocar las primeras 3 columnas de datos
        prod_row = 1
        prod_col = 0
        Num=1
        for i in get_diario_Factura:
            sheet.write(prod_row, prod_col, 3, txt)
            sheet.write(prod_row, prod_col+1, Num, txt)
            sheet.write(prod_row, prod_col + 2, i['fecha_factura'], txt)
            sheet.write(prod_row, prod_col + 3, int(i['numero_factura']), txt)
            sheet.write(prod_row, prod_col + 4, int(i['N_de_autorizacion']), txt)
            sheet.write(prod_row, prod_col + 5, i['estado'], txt)
            sheet.write(prod_row, prod_col + 6, int(i['NIT']), txt)
            sheet.write(prod_row, prod_col + 7, i['razon_social'], txt)
            #formato de celda 2 decimales
            sheet.write(prod_row, prod_col + 8, i['importe_total'], txt)
            sheet.write(prod_row, prod_col + 9, i['importe_ice'], txt)
            sheet.write(prod_row, prod_col + 10, i['exportaciones_operaciones_exentas'], txt)
            sheet.write(prod_row, prod_col + 11, i['ventas_agravadas_a_tasa_cero'], txt)
            sheet.write(prod_row, prod_col + 12, i['subtotal'], txt)
            sheet.write(prod_row, prod_col + 13, i['descuentos'], txt)
            sheet.write(prod_row, prod_col + 14, i['importe_base_para_debito_fiscal'], txt)
            sheet.write(prod_row, prod_col + 15, i['debito_fiscal'], txt)
            sheet.write(prod_row, prod_col + 16, i['codigo_de_control'], txt)
            prod_row += 1
            Num += 1
        sheet.set_column(0, 0, 15)
        sheet.set_column(2, 4, 15)
        sheet.set_column(6, 11, 26)
        sheet.set_column(13, 16, 26)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


    def generate_file_2(self):
        wh = self.diario_venta.mapped('id')
        obj = self.env['account.move'].search([('journal_id', 'in', wh) or ('type', '=', 'out_invoice')])
        # filtrar estado publicaco y anulado
        obj2 = self.filtro_estado(obj)
        obj3 = self.ordenar_por_diario_y_menor_a_mayor(obj2, wh)
        # por hacer filtro de codigo de control si es factura computarizada
        nuevo_obejto_factura = []
        for i in self.filtrar_por_fecha(obj3, self):
            vals = {
                'numero_factura': i.fcb_numero_factura_computarizada or self.get_numero_factura(i.name),
                'fecha_factura': i.invoice_date.strftime("%d/%m/%Y"),
                'N_de_autorizacion': i.journal_id.fcb_numero_autorizacion_diario,
                'estado': 'V' if i.state == 'posted' else 'A',
                'NIT': (i.fcb_nit_a_facturar or (i.partner_id.vat or 0) ) if i.state == 'posted' else 0,
                'razon_social': (i.fcb_nombre_a_facturar or i.partner_id.name) if i.state == 'posted' else 'ANULADA',
                'importe_total': i.amount_total if i.state == 'posted' else 0,
                # advertencia si realiza una modificacion realice la operaciones correspondientes
                'importe_ice': 0,
                'exportaciones_operaciones_exentas': 0,
                'ventas_agravadas_a_tasa_cero': 0,
                # subtotal = importe_total-importe ice - exportaciones y operaciones exentas -ventas agravadas a tasa cero
                'subtotal': i.amount_total if i.state == 'posted' else 0,
                'descuentos': 0,
                # importe_base_para_debito_fiscal = subtotal - descuento , como no existe descuento realizamos el siguiente codigo
                'importe_base_para_debito_fiscal': i.amount_total if i.state == 'posted' else 0,
                # debito fiscal = importe_base_para_debito_fiscal *13%
                'debito_fiscal': round((i.amount_total * 13) / 100 if i.state == 'posted' else 0,2),
                'codigo_de_control': self.cambiar_o_por_0_codigo_control(i) if self.cambiar_o_por_0_codigo_control(
                    i) else 0,
            }
            nuevo_obejto_factura.append(vals)
        Num = 1
        content = ''
        for i in nuevo_obejto_factura:
            content += '3' + '|' + str(Num) + '|' + i['fecha_factura'] + '|' + str(int(i['numero_factura'])) + '|' + \
                     str(i['N_de_autorizacion']) + '|' + i['estado'] + '|' + str(i['NIT']) + '|' +str(i['razon_social']) + '|' + str(i['importe_total']) + '|' + str(i['importe_ice']) + '|' + str(
                    i['exportaciones_operaciones_exentas']) + '|' + str(i['ventas_agravadas_a_tasa_cero']) +'|' + str(i['subtotal']) + '|' + str(i['descuentos']) + '|' + str(
                    i['importe_base_para_debito_fiscal']) + '|' + str(i['debito_fiscal']) + '|' + str(
                    i['codigo_de_control']) + '\n'
            Num += 1
        export_id = self.env['txt.report'].create(
            {'txt_binary': base64.encodestring(content.encode()).decode().strip(), 'txt_filename':  'Libro venta.txt'})
        res = {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'txt.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res


