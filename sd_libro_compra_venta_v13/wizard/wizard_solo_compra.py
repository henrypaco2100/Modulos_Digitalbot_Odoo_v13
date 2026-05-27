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

_logger = logging.getLogger(__name__)


class SdWizardCompraVenta(models.Model):
    _name = 'wizard.solo.compra'

    estado = fields.Selection([('posted', 'Publicados'),
                              ('todos', 'Todos')
                              ], string='Estado', default='posted', track_visibility='onchange')
    diario = fields.Many2many('account.journal', string="diario",
                              domain="[('type', '=', 'purchase')]")
    fecha_inicio = fields.Date(string="Fecha inicio", required=False)
    fecha_fin = fields.Date(string="Fecha fin", required=False)
    CAF = fields.Selection([('publicados', 'Publicados'),
                              ('todos', 'Todos')
                              ], string='CAF', default='publicados', track_visibility='onchange')
    # tipo = fields.Selection([('compra', 'Compra'), ('venta', 'Venta')], string='Tipo', track_visibility='onchange',
    #                         required=True)
    excel_file = fields.Binary('Reporte Excel')
    file_name = fields.Char('Archivo Excel', size=64)

    def print_solo_compra(self):
        reporte = self.imprimir_reporte_compra()
        return reporte

    def imprimir_reporte_compra(self):
        if (self.fecha_fin and self.fecha_inicio) and (self.fecha_fin < self.fecha_inicio):
            raise UserError('Los rangos de fechas son incoherentes')

        datos_report = self.get_datos_report()
        # print('datos_report: ', datos_report)
        reporte = xlwt.Workbook(style_compression=2)

        worksheet1 = reporte.add_sheet('sheet_1', cell_overwrite_ok=True)
        style_header = xlwt.easyxf("font: color black, bold on; align: vert center,horiz center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour grey25")
        worksheet1.row(0).height = 500
        for i in range(25):
            worksheet1.col(i).width = 5000
        worksheet1.col(0).width = 1300
        worksheet1.col(3).width = 10000
        worksheet1.col(4).width = 7000
        worksheet1.col(15).width = 8000
        worksheet1.col(17).width = 9000

        worksheet1.write(0, 0, 'Nro', style_header)
        worksheet1.write(0, 1, 'ESPECIFICACION', style_header)
        worksheet1.write(0, 2, 'NIT PROVEEDOR', style_header)
        worksheet1.write(0, 3, 'RAZON SOCIAL PROVEEDOR', style_header)
        worksheet1.write(0, 4, 'CODIGO DE AUTORIZACION', style_header)
        worksheet1.write(0, 5, 'NUMERO FACTURA', style_header)
        worksheet1.write(0, 6, 'NUMERO DUI/DIM', style_header)
        worksheet1.write(0, 7, 'FECHA DE \nFACTURA/DUI/DIM', style_header)
        worksheet1.write(0, 8, 'IMPORTE TOTAL \nCOMPRA', style_header)
        worksheet1.write(0, 9, 'IMPORTE ICE', style_header)
        worksheet1.write(0, 10, 'IMPORTE IEHD', style_header)
        worksheet1.write(0, 11, 'IMPORTE IPJ', style_header)
        worksheet1.write(0, 12, 'TASAS', style_header)
        worksheet1.write(0, 13, 'OTRO NO SUJETO A \nCREDITO FISCAL', style_header)
        worksheet1.write(0, 14, 'IMPORTES \nEXENTOS', style_header)
        worksheet1.write(0, 15, 'IMPORTE COMPRAS GRAVADAS \nA TASA CERO', style_header)
        worksheet1.write(0, 16, 'SUBTOTAL', style_header)
        worksheet1.write(0, 17, 'DESCUENTOS/ BONIFICACIONES Y \nREBAJAS SUJETAS AL IVA', style_header)
        worksheet1.write(0, 18, 'IMPORTE GIFT CARD', style_header)
        worksheet1.write(0, 19, 'IMPORTE BASE CF', style_header)
        worksheet1.write(0, 20, 'CREDITO FISCAL', style_header)
        worksheet1.write(0, 21, 'TIPO COMPRA', style_header)
        worksheet1.write(0, 22, 'CODIGO DE \nCONTROL', style_header)
        countrow = 1

        # IMPRIMIR DATOS
        for dato in datos_report:
            especificacion = 1
            ice = 0
            iehd = 0
            ipj = 0
            tasas = 0
            no_cred_fiscal = 0
            imp_exentos = 0
            grab = 0
            gift_card = 0
            cod_ctrl = 0
            tipo_compra = 0
            numero_dui = dato.sd_numero_dui
            razon_social = dato.partner_id.name
            cod_autorizacion = dato.fcb_autorizacion_compra
            total_compra = 0
            desc_suj_iva = 0
            subtotal = 0


            # if dato.partner_id.sd_codigo_tipo_documento == '1':
            #     complemento = dato.partner_id.sd_extension

            for line in dato.invoice_line_ids:
                total_compra += line.quantity * line.price_unit
                subtotal += line.price_subtotal
                # precio_unitario = round((self.validar_campos_factura(line)) / tipo_cambio, 2)
                # monto_descuento = round((line.discount * precio_unitario) / 100, 2)

            if dato.sd_es_giftcard:
                gift_card = dato.sd_cantidad_gift_card

            if dato.fcb_tipo_compra:
                especificacion = dato.fcb_numero_dim

            if dato.partner_id.st_nombre_compañia_facturar:
                razon_social = dato.partner_id.st_nombre_compañia_facturar

            if not dato.fcb_autorizacion_compra:
                cod_autorizacion = dato.fcb_cuf
                if not dato.fcb_cuf:
                    cod_autorizacion = ''

            if dato.fcb_codigo_control_compra:
                cod_ctrl = dato.fcb_codigo_control_compra

            prueba = dato.fcb_tipo_compra
            # print('tipo compra: ', prueba)
            if prueba == 'compra_interno_gravadas':
                tipo_compra = 1
            if prueba == 'compra_interno_no_gravadas':
                tipo_compra = 2
            if prueba == 'compra_proporcionalidad':
                tipo_compra = 3
            if prueba == 'compra_exportaciones':
                tipo_compra = 4
            if prueba == 'compra_interno_exportaciones':
                tipo_compra = 5


            # subtotal = round((precio_unitario * line.quantity - monto_descuento), 2)

            fecha_cadena = str(dato.date)[-2:] + '-' + str(dato.date)[5:7] + '-' + str(dato.date)[:4]

            worksheet1.write((countrow), 0, str(countrow), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 1, str(especificacion), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 2, str(dato.partner_id.vat), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 3, razon_social, xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 4, cod_autorizacion, xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 5, str(dato.fcb_numero_factura), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 6, numero_dui, xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 7, fecha_cadena, xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 8, str(round(total_compra)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 9, str(round(ice, 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 10, str(round(iehd, 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 11, str(round(ipj, 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 12, str(round(tasas, 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 13, str(round(no_cred_fiscal, 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 14, str(round(imp_exentos, 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 15, str(round(grab, 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))

            #subtotal revisar
            worksheet1.write((countrow), 16, str(round(subtotal, 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))

            worksheet1.write((countrow), 17, str(round(desc_suj_iva, 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 18, str(round(gift_card, 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 19, str(round((subtotal - desc_suj_iva - gift_card), 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 20, str(round((subtotal * 0.13), 2)), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 21, str(tipo_compra), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))
            worksheet1.write((countrow), 22, str(cod_ctrl), xlwt.easyxf("borders: left thin, right thin, bottom thin; align: horiz centre"))

            countrow += 1



        fp = io.BytesIO()
        reporte.save(fp)
        self.write({'excel_file': base64.encodestring(fp.getvalue()), 'file_name': 'Planilla registro compras.xls'})
        res = {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'wizard.solo.compra',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res

    def get_datos_report(self):
        consulta_ini = ('date', '!=', None)
        consulta_fin = ('date', '!=', None)
        if self.fecha_inicio:
            consulta_ini = ('date', '>=', self.fecha_inicio)
        if self.fecha_fin:
            consulta_fin = ('date', '<=', self.fecha_fin)
        if self.estado and self.estado != 'todos':
            consulta_estado = ('state', '=', self.estado)
        else:
            consulta_estado = ('state', 'in', ['posted', 'cancel'])
        list_diario = []
        diario = self.diario
        if not self.diario:
            diario = self.env['account.journal'].search([('type', '=', 'purchase')])
        for item_diario in diario:
            list_diario.append(item_diario.id)
        # print('list diario: ', list_diario)
        move_ids = self.env['account.move'].search([('type', '=', 'in_invoice'), ('journal_id', 'in', list_diario), consulta_ini, consulta_fin, consulta_estado], order='date asc')
        return move_ids

    def validar_campos_factura(self, factura):
        if factura.quantity and factura.price_unit:
            return factura.price_unit
        return 0

    def invertir_fecha(self, cadena):
        fecha_invertida = cadena[-2:] + '-' + cadena[5:7] + '-' + cadena[:4]
        return fecha_invertida


