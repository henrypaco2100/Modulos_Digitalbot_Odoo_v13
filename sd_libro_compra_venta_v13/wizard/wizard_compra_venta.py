 # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from itertools import groupby
import xlwt
import base64
import io
import xlsxwriter
from datetime import datetime, time, timedelta
import pytz
from odoo import fields
_logger = logging.getLogger(__name__)


class SdWizardCompraVenta(models.Model):
    _name = 'wizard.compra.venta'

    estado = fields.Selection([('posted', 'Publicados'),
                              ('todos', 'Todos')
                              ], string='Estado', default='posted', track_visibility='onchange')
    diario = fields.Many2many('account.journal', string="diario",
                              domain="['&', ('type', '=', 'sale'), ('fcb_es_electronico', '=', True)]")
    fecha_inicio = fields.Date(string="Fecha inicio", required=False)
    fecha_fin = fields.Date(string="Fecha fin", required=False)
    CAF = fields.Selection([('publicados', 'Publicados'),
                              ('todos', 'Todos')
                              ], string='CAF', default='publicados', track_visibility='onchange')
    # tipo = fields.Selection([('compra', 'Compra'), ('venta', 'Venta')], string='Tipo', track_visibility='onchange',
    #                         required=True)
    excel_file = fields.Binary('Reporte Excel')
    file_name = fields.Char('Archivo Excel', size=64)

    def print_report_compra_venta(self):
        reporte = self.imprimir_reporte()
        return reporte

    def imprimir_reporte(self):
        if (self.fecha_fin and self.fecha_inicio) and (self.fecha_fin < self.fecha_inicio):
            raise UserError('Los rangos de fechas son incoherentes')
        # if not self.tipo:
        #     raise UserError('El tipo debe estar registrado, ultima ves >:|')

        datos_report = self.get_datos_report()
        # print('datos_report: ', datos_report)
        reporte = xlwt.Workbook(style_compression=2)

        worksheet1 = reporte.add_sheet('sheet_1', cell_overwrite_ok=True)
        style_header = xlwt.easyxf("font: color black, bold on; align: vert center,horiz center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour grey25")
        style_kardex_numeric = xlwt.easyxf(
            "font: name Calibri, height 200, color black; align: horiz right; borders: left thin, right thin, bottom thin")
        style_kardex_numeric.num_format_str = '#,##0.00'
        worksheet1.row(0).height = 500
        for i in range(25):
            worksheet1.col(i).width = 7000
        worksheet1.col(0).width = 1200
        worksheet1.col(3).width = 5000
        worksheet1.col(4).width = 17000
        worksheet1.col(5).width = 5000
        worksheet1.col(7).width = 12000
        worksheet1.col(8).width = 5000
        worksheet1.col(9).width = 5000
        worksheet1.col(10).width = 5000
        worksheet1.col(11).width = 5000
        worksheet1.col(12).width = 5000
        worksheet1.col(16).width = 5000
        worksheet1.col(17).width = 8500
        worksheet1.col(18).width = 5000
        worksheet1.col(20).width = 5000
        worksheet1.col(21).width = 5000



        worksheet1.write(0, 0, 'Nro', style_header)
        worksheet1.write(0, 1, 'ESPECIFICACION', style_header)
        worksheet1.write(0, 2, 'FECHA DE LA FACTURA', style_header)
        worksheet1.write(0, 3, 'Nro DE LA FACTURA', style_header)
        worksheet1.write(0, 4, 'CODIGO DE AUTORIZACION', style_header)
        worksheet1.write(0, 5, 'NIT / CI CLIENTE', style_header)
        worksheet1.write(0, 6, 'COMPLEMENTO', style_header)
        worksheet1.write(0, 7, 'NOMBRE O RAZON SOCIAL', style_header)
        worksheet1.write(0, 8, 'IMPORTE TOTAL \nDE LA VENTA', style_header)
        worksheet1.write(0, 9, 'IMPORTE ICE', style_header)
        worksheet1.write(0, 10, 'IMPORTE IEHD', style_header)
        worksheet1.write(0, 11, 'IMPORTE IPJ', style_header)
        worksheet1.write(0, 12, 'TASAS', style_header)
        worksheet1.write(0, 13, 'OTROS NO SUJETOS AL IVA', style_header)
        worksheet1.write(0, 14, 'EXPORTACIONES Y \nOPERACIONES EXTERNAS', style_header)
        worksheet1.write(0, 15, 'VENTAS GRABADAS A \nTASA CERO', style_header)
        worksheet1.write(0, 16, 'SUBTOTAL', style_header)
        worksheet1.write(0, 17, 'DESCUENTOS BONIFICACIONES Y \nREBAJAS SUJETAS AL IVA', style_header)
        worksheet1.write(0, 18, 'IMPORTE GIFT CARD', style_header)
        worksheet1.write(0, 19, 'IMPORTE BASE PARA \nDEBITO FISCAL', style_header)
        worksheet1.write(0, 20, 'DEBITO FISCAL', style_header)
        worksheet1.write(0, 21, 'ESTADO', style_header)
        worksheet1.write(0, 22, 'CODIGO DE CONTROL', style_header)
        worksheet1.write(0, 23, 'TIPO DE VENTA', style_header)
        # worksheet1.write(0, 23, 'CON DERECHO A \nCREDITO FISCAL', style_header)
        # worksheet1.write(0, 24, 'ESTADO CONSOLIDACION', style_header)

        countrow = 1
        # IMPRIMIR DATOS
        for dato in datos_report:
            especificacion = '2'
            ice = 0
            iehd = 0
            ipj = 0
            tasas = 0
            no_iva = 0
            export = 0
            grab = 0
            gift_card = 0
            cod_ctrl = 0
            tipo_venta = 0
            complemento = ''
            tipo_cambio = dato.currency_id.rate
            estado = dato.state
            subtotal = 0
            for line in dato.invoice_line_ids:
                # subtotal += line.quantity * line.price_unit
                precio_unitario = round((self.validar_campos_factura(line)) / tipo_cambio, 2)
                monto_descuento = round((line.discount * precio_unitario * line.quantity) / 100, 2)
                subtotal += round((precio_unitario * line.quantity - monto_descuento), 2)

            if dato.sd_es_giftcard:
                gift_card = dato.sd_cantidad_gift_card
                tipo_venta = 1
            # subtotal = round((precio_unitario * line.quantity - monto_descuento), 2)

            #revisamos si el tipo de documento del cliente es CI - CEDULA DE IDENTIDAD
            if dato.partner_id.sd_codigo_tipo_documento == '1':
                if dato.partner_id.sd_extension:
                    complemento = dato.partner_id.sd_extension

            if dato.sd_nro_importacion:
                especificacion = dato.sd_nro_importacion

            if estado == 'posted': estado = 'VALIDA'
            if dato.sd_is_offline: estado = 'EMITIDA EN CONTINGENCIA'
            if estado == 'cancel': estado = 'CANCELADO'

            fecha_cadena = str((dato.sd_fecha_emision - timedelta(hours=4)).date())
            worksheet1.write((countrow), 0, str(countrow), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 1, especificacion, xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 2, self.invertir_fecha(fecha_cadena), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 3, dato.sd_nro_factura_siat,xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 4, dato.sd_cuf, xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 5, str(dato.sd_nro_documento_facturado), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 6, complemento, xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 7, dato.sd_nombre_facturado or dato.partner_id.name, xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 8, round(dato.amount_total, 2), style_kardex_numeric)
            worksheet1.write((countrow), 9, round(ice, 2), style_kardex_numeric)
            worksheet1.write((countrow), 10, round(iehd, 2), style_kardex_numeric)
            worksheet1.write((countrow), 11, round(ipj, 2), style_kardex_numeric)
            worksheet1.write((countrow), 12, round(tasas, 2), style_kardex_numeric)
            worksheet1.write((countrow), 13, round(no_iva, 2), style_kardex_numeric)
            worksheet1.write((countrow), 14, round(export, 2), style_kardex_numeric)
            worksheet1.write((countrow), 15, round(grab, 2), style_kardex_numeric)
            worksheet1.write((countrow), 16, round((subtotal - ice - iehd - ipj - tasas - no_iva - export - grab), 2), style_kardex_numeric)
            worksheet1.write((countrow), 17, round(dato.sd_descuento_adicional, 2), style_kardex_numeric)
            worksheet1.write((countrow), 18, round(gift_card, 2), style_kardex_numeric)
            worksheet1.write((countrow), 19, round((subtotal - dato.sd_descuento_adicional - gift_card), 2), style_kardex_numeric)
            worksheet1.write((countrow), 20, round((subtotal * 0.13), 2), style_kardex_numeric)
            worksheet1.write((countrow), 21, estado, xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 22, str(cod_ctrl), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 23, str(tipo_venta), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))

            countrow += 1



        fp = io.BytesIO()
        reporte.save(fp)
        self.write({'excel_file': base64.encodestring(fp.getvalue()), 'file_name': 'Planilla registro ventas.xls'})
        res = {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'wizard.compra.venta',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res

    def get_datos_report(self):
        consulta_ini = ('sd_fecha_emision', '!=', None)
        consulta_fin = ('sd_fecha_emision', '!=', None)
        fecha_datetime_ini = datetime.combine(self.fecha_inicio, time.min)
        fecha_datetime_fin = datetime.combine(self.fecha_fin, time.max)

        fecha_datetime_ini += timedelta(hours=4)
        fecha_datetime_fin += timedelta(hours=4)
        if fecha_datetime_ini:
            consulta_ini = ('sd_fecha_emision', '>=', fecha_datetime_ini)
        if fecha_datetime_fin:
            consulta_fin = ('sd_fecha_emision', '<=', fecha_datetime_fin)
        if self.estado and self.estado != 'todos':
            consulta_estado = ('state', '=', self.estado)
        else:
            consulta_estado = ('state', 'in', ['posted', 'cancel'])

        list_diario = []
        diario = self.diario
        if not self.diario:
            diario = self.env['account.journal'].search([('type', '=', 'sale'), ('fcb_es_electronico', '=', True)])
        for item_diario in diario:
            list_diario.append(item_diario.id)

        #LA BUSQUESA DE JOURNAL_ID SOLO FUNCION CON DIARIO VENTA..POR ALGUNA RAZON..
        move_ids = self.env['account.move'].search([('journal_id', 'in', list_diario), ('type', '=', 'out_invoice'),
                                                    consulta_ini, consulta_fin, consulta_estado], order='sd_nro_factura_siat asc')
        return move_ids

    def validar_campos_factura(self, factura):
        if factura.quantity and factura.price_unit:
            return factura.price_unit
        return 0

    def invertir_fecha(self, cadena):
        fecha_invertida = cadena[-2:] + '-' + cadena[5:7] + '-' + cadena[:4]
        return fecha_invertida


