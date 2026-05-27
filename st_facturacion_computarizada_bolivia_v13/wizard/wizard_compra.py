import json
import base64
import datetime
import os
import io
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class FacturaVentaReporte(models.TransientModel):
    _name = "factura.compra.reporte"
    _description = "Historial de las factura tipo venta"

    diario_compra = fields.Many2many('account.journal', required=True, string='Diario',domain="[('type','=','purchase')]")
    fecha_inicio = fields.Date(string='Fecha de inicio')
    fecha_final = fields.Date(string='Fecha final')
    def export_xls_compra(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'diario': self.diario_compra.ids,
            'fecha_inicio': self.fecha_inicio,
            'fecha_final': self.fecha_final,
        }
        return {
            'type': 'ir_actions_xlsx_download_libro',
            'data': {'model': 'factura.compra.reporte',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Libro de Compra',
                     }
        }
    def get_diario_Factura_compra(self, data):
        wh = data.diario_compra.mapped('id')
        obj = self.env['account.move'].search([('journal_id', 'in', wh) or ('type','=','in_invoice')])
        # filtrar estado publicaco y anulado
        obj2 = self.filtro_estado(obj)
        obj3= self.ordenar_por_diario_y_menor_a_mayor(obj2,wh)
        # por hacer filtro de codigo de control si es factura computarizada
        nuevo_obejto_factura=[]
        for i in self.filtrar_por_fecha(obj3,data):          #self.filtrar_por_fecha(obj3,data):
            b = 0
            D =0
            vals={

                'numero_factura': self.get_numero_factura(i.name),
                'fecha_factura': i.invoice_date.strftime("%d/%m/%Y"),
                'NIT': i.partner_id.vat if i.partner_id.vat else 0,
                'razon_social': i.partner_id.name,
                'n_dui': i.fcb_numero_dim if i.fcb_numero_dim else 0,
                'N_de_autorizacion': i.fcb_autorizacion_compra,
                'importe_total': i.amount_total if i.amount_total else 0,
                'importe_no_sujeto_a_credito_fiscal': b,
                # subtotal = importe total - importe no sujeto a credito fiscal (c=a-b)
                'subtotal':  i.amount_total - b,
                'descuentos': D,
                # importe_base_para_credito_fiscal = subtotal - descuento (E=C-D)
                'importe_base_para_credito_fiscal': (i.amount_total - b) - D,
                #credito fiscal = importe_base_para_debito_fiscal *13%
                'credito_fiscal':round((((i.amount_total - b) - D)*13)/100,2),
                'codigo_de_control': self.cambiar_o_por_0_codigo_control(i),
                'tipo_de_compra': self.tipo_de_compra(i)
            }
            nuevo_obejto_factura.append(vals)
        return nuevo_obejto_factura
    def tipo_de_compra(self,factura):
        diccionario ={
            'compra_interno_gravadas': 1, 'compra_interno_no_gravadas': 2,
            'compra_proporcionalidad': 3, 'compra_exportaciones': 4, 'compra_interno_exportaciones': 5
        }
        if factura.fcb_tipo_compra:
            if factura.fcb_tipo_compra in diccionario:
                return diccionario[factura.fcb_tipo_compra]
        else:
            return ''
    def cambiar_o_por_0_codigo_control(self,factura):
        nuevo_codigo_control = ''
        if factura.fcb_codigo_control_compra:
            for caracter in factura.fcb_codigo_control_compra:
                if caracter == 'O':
                    nuevo_codigo_control = nuevo_codigo_control+'0'
                else:
                    nuevo_codigo_control = nuevo_codigo_control+caracter
            return nuevo_codigo_control
        else:
            return 0
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
    def filtro_estado(self,objetos_facturas):
        nuevo_objeto_factura = []
        for factura in objetos_facturas:
            if factura.state == 'posted':
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
        get_diario_Factura = self.get_diario_Factura_compra(lines)
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('libro de compra')
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px'})
        sheet.write(0, 0, 'ESPECIFICACIÓN', cell_format)
        sheet.write(0, 1,  'Nº', cell_format)
        sheet.write(0, 2, 'FECHA DE LA FACTURA DUI', cell_format)
        sheet.write(0, 3, 'NIT PROVEEDOR', cell_format)
        sheet.write(0, 4, 'NOMBRE Y APELLIDO/RAZON SOCIAL', cell_format)
        sheet.write(0, 5, 'Nº DE LA FACTURA', cell_format)
        sheet.write(0, 6, 'Nº DE DUI', cell_format)
        sheet.write(0, 7, 'Nº DE AUTORIZACION', cell_format)
        sheet.write(0, 8, 'IMPORTE TOTAL DE LA COMPRA', cell_format)
        sheet.write(0, 9, 'IMPORTE NO SUJETO A CRÉDITO FISCAL', cell_format)
        sheet.write(0, 10, 'SUBTOTAL', cell_format)
        sheet.write(0, 11, 'DESCUENTOS, BONIFICACIONES Y REBAJAS OBTENIDAS', cell_format)
        sheet.write(0, 12, 'IMPORTE BASE PARA CRÉDITO FISCAL', cell_format)
        sheet.write(0, 13, 'CRÉDITO FISCAL', cell_format)
        sheet.write(0, 14, 'CODIGO CONTROL', cell_format)
        sheet.write(0, 15, 'TIPO DE COMPRA', cell_format)

        #colocar las primeras 3 columnas de datos
        prod_row = 1
        prod_col = 0
        Num=1
        for i in get_diario_Factura:
            sheet.write(prod_row, prod_col, 1, txt)
            sheet.write(prod_row, prod_col+1, Num, txt)
            sheet.write(prod_row, prod_col + 2,i['fecha_factura'], txt)
            sheet.write(prod_row, prod_col + 3, int(i['NIT']), txt)
            sheet.write(prod_row, prod_col + 4, i['razon_social'], txt)
            sheet.write(prod_row, prod_col + 5, int(i['numero_factura']), txt)
            sheet.write(prod_row, prod_col + 6, i['n_dui'], txt)
            sheet.write(prod_row, prod_col + 7, int(i['N_de_autorizacion']), txt)
            sheet.write(prod_row, prod_col + 8, int(i['importe_total']), txt)
            sheet.write(prod_row, prod_col + 9, int(i['importe_no_sujeto_a_credito_fiscal']), txt)
            sheet.write(prod_row, prod_col + 10, int(i['subtotal']), txt)
            sheet.write(prod_row, prod_col + 11, int(i['descuentos']), txt)
            sheet.write(prod_row, prod_col + 12, int(i['importe_base_para_credito_fiscal']), txt)
            sheet.write(prod_row, prod_col + 13, int(i['credito_fiscal']), txt)
            sheet.write(prod_row, prod_col + 14, i['codigo_de_control'], txt)
            sheet.write(prod_row, prod_col + 15, i['tipo_de_compra'], txt)

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
    def generate_file_compra(self):
        wh = self.diario_compra.mapped('id')
        obj = self.env['account.move'].search([('journal_id', 'in', wh) or ('type', '=', 'in_invoice')])
        # filtrar estado publicaco y anulado
        obj2 = self.filtro_estado(obj)
        obj3 = self.ordenar_por_diario_y_menor_a_mayor(obj2, wh)
        # por hacer filtro de codigo de control si es factura computarizada
        nuevo_obejto_factura = []
        for i in self.filtrar_por_fecha_txt(obj3):
            b = 0
            D = 0
            vals = {

                'numero_factura':self.get_numero_factura(i.name),
                'fecha_factura': i.invoice_date.strftime("%d/%m/%Y"),
                'NIT': i.partner_id.vat if i.partner_id.vat else 0,
                'razon_social': i.partner_id.name,
                'n_dui': i.fcb_numero_dim if i.fcb_numero_dim else 0,
                'N_de_autorizacion':i.fcb_autorizacion_compra if i.fcb_autorizacion_compra else 0,
                'importe_total': i.amount_total if i.amount_total else 0,
                'importe_no_sujeto_a_credito_fiscal': b,
                # subtotal = importe total - importe no sujeto a credito fiscal (c=a-b)
                'subtotal': i.amount_total - b,
                'descuentos': D,
                # importe_base_para_credito_fiscal = subtotal - descuento (E=C-D)
                'importe_base_para_credito_fiscal': (i.amount_total - b) - D,
                # credito fiscal = importe_base_para_debito_fiscal *13%
                'credito_fiscal': round((((i.amount_total - b) - D) * 13) / 100,2),
                'codigo_de_control': self.cambiar_o_por_0_codigo_control(i),
                'tipo_de_compra': self.tipo_de_compra(i)
            }
            nuevo_obejto_factura.append(vals)
        Num = 1
        content = ''
        for i in nuevo_obejto_factura:
            content += '1' + '|' + str(Num) + '|' + i['fecha_factura'] + '|' + str(i['NIT']) + '|' + \
                       str(i['razon_social']) + '|' + str(int(i['numero_factura'])) + '|' + str(i['n_dui']) + '|' + str(
                i['N_de_autorizacion']) + '|' + str(i['importe_total']) + '|' + str(i['importe_no_sujeto_a_credito_fiscal']) + '|' + str(
                i['subtotal']) + '|' + str(i['descuentos']) + '|' + str(
                i['importe_base_para_credito_fiscal']) + '|' + str(i['credito_fiscal']) + '|' + str(
                i['codigo_de_control']) + '|' + str(i['tipo_de_compra']) + '|' + '\n'
            Num += 1
        export_id = self.env['txt.report'].create(
            {'txt_binary': base64.encodestring(content.encode()).decode().strip(), 'txt_filename': 'Libro compra.txt'})
        res = {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'txt.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res
    def filtrar_por_fecha_txt(self, objeto_Factura):
        nuevo_obejto_filtrado=[]
        if self.fecha_inicio or self.fecha_final:
            if self.fecha_inicio and self.fecha_final:
                #ambos existen
                if self.fecha_inicio <= self.fecha_final:
                    for factura in objeto_Factura:
                        if self.fecha_inicio <= factura.invoice_date <= self.fecha_final:
                            nuevo_obejto_filtrado.append(factura)
                else:
                    raise UserError('La fecha de finalización debe ser mayor que la fecha de inicio.')
            elif self.fecha_inicio:
                #fecha inicio existe
                for factura in objeto_Factura:
                    if self.fecha_inicio <= factura.invoice_date:
                        nuevo_obejto_filtrado.append(factura)
            else:
                #fecha final existe
                for factura in objeto_Factura:
                    if factura.invoice_date <= self.fecha_final:
                        nuevo_obejto_filtrado.append(factura)
        else:
            # no existe ninguno de los dos
            nuevo_obejto_filtrado = objeto_Factura
        return nuevo_obejto_filtrado