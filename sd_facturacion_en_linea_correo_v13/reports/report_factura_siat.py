from odoo import api, fields, models, _
import qrcode
import base64
from datetime import datetime, timedelta, time
from io import BytesIO
from pysiat import constants
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
class SdInheritAccountMoveCorreoSiatReport(models.Model):
    _inherit = 'account.move'

    sd_prueba_campo = fields.Char()

    def es_tasa_cero(self):
        return int(self.sd_codigo_documento_sector) == constants.TiposDocumentoSector.FACTURA_TASA_CERO_LIBROS
    def get_nro_factura(self):
        return self.sd_nro_factura_siat if not self.es_debito_credito() else self.sd_nro_debito_credito
    def obtener_sucursal_report(self):
        if self.journal_id.sd_factura_online_id.sd_codigo_sucursal:
            # resultado = dict(self.journal_id.sd_factura_online_id._fields['sd_codigo_sucursal'].selection).get(self.journal_id.sd_factura_online_id.sd_codigo_sucursal)
            resultado = self.env['sucursal.factura.siat'].search([('sd_codigo_clasificador', '=', self.journal_id.sd_factura_online_id.sd_codigo_sucursal)]).sd_descripcion
            return resultado
    def obtener_nro_punto_venta(self):
        if self.journal_id.sd_factura_online_id.sd_es_punto_venta:
            if self.journal_id.sd_factura_online_id.sd_codigo_punto_venta:
                return " " + str(self.journal_id.sd_factura_online_id.sd_codigo_punto_venta.sd_codigo_punto_venta)
        else:
            resultado = '0'
            return " " +resultado
    def obtener_direccion(self):
        if self.journal_id.sd_factura_online_id.sd_direccion:
            return self.journal_id.sd_factura_online_id.sd_direccion
    def obtener_municipio(self):
        if self.journal_id.sd_factura_online_id.sd_municipio:
            return self.journal_id.sd_factura_online_id.sd_municipio

    def numero_to_letras(self, numero):
        indicador = [("", ""), ("MIL", "MIL"), ("MILLON", "MILLONES"), ("MIL", "MIL"), ("BILLON", "BILLONES")]
        entero = int(numero)
        decimal = int(round((numero - entero) * 100))
        # print 'decimal : ',decimal
        contador = 0
        numero_letras = ""
        while entero > 0:
            a = entero % 1000
            if contador == 0:
                en_letras = self.convierte_cifra(a, 1).strip()
            else:
                en_letras = self.convierte_cifra(a, 0).strip()
            if a == 0:
                numero_letras = en_letras + " " + numero_letras
            elif a == 1:
                if contador in (1, 3):
                    numero_letras = indicador[contador][0] + " " + numero_letras
                else:
                    numero_letras = en_letras + " " + indicador[contador][0] + " " + numero_letras
            else:
                numero_letras = en_letras + " " + indicador[contador][1] + " " + numero_letras
            numero_letras = numero_letras.strip()
            contador = contador + 1
            entero = int(entero / 1000)
        # print('numero literal', numero_letras)
        if numero_letras == '':
            numero_letras = 'CERO'
        diccionario_Decimal = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
        if decimal in diccionario_Decimal:
            numero_letras = numero_letras + " " + '0' + str(decimal) + "/100"

        else:
            numero_letras = numero_letras + " " + str(decimal) + "/100"

        return numero_letras

    def convierte_cifra(self, numero, sw):
        lista_centana = ["", ("CIEN", "CIENTO"), "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS",
                         "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]
        lista_decena = ["", (
            "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE"),
                        ("VEINTE", "VEINTI"), ("TREINTA", "TREINTA Y "), ("CUARENTA", "CUARENTA Y "),
                        ("CINCUENTA", "CINCUENTA Y "), ("SESENTA", "SESENTA Y "),
                        ("SETENTA", "SETENTA Y "), ("OCHENTA", "OCHENTA Y "),
                        ("NOVENTA", "NOVENTA Y ")
                        ]
        lista_unidad = ["", ("UN", "UNO"), "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"]
        centena = int(numero / 100)
        decena = int((numero - (centena * 100)) / 10)
        unidad = int(numero - (centena * 100 + decena * 10))
        # print "centena: ",centena, "decena: ",decena,'unidad: ',unidad

        texto_centena = ""
        texto_decena = ""
        texto_unidad = ""

        # Validad las centenas
        texto_centena = lista_centana[centena]
        if centena == 1:
            if (decena + unidad) != 0:
                texto_centena = texto_centena[1]
            else:
                texto_centena = texto_centena[0]

        # Valida las decenas
        texto_decena = lista_decena[decena]
        if decena == 1:
            texto_decena = texto_decena[unidad]
        elif decena > 1:
            if unidad != 0:
                texto_decena = texto_decena[1]
            else:
                texto_decena = texto_decena[0]
        # Validar las unidades
        # print "texto_unidad: ",texto_unidad
        if decena != 1:
            texto_unidad = lista_unidad[unidad]
            if unidad == 1:
                texto_unidad = texto_unidad[sw]
        return "%s %s %s" % (texto_centena, texto_decena, texto_unidad)

    def generate_factura_qr_siat(self):
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=20, border=4, )
        qr.add_data(
            self.sd_url_factura
        )
        qr.make(fit=True)

        img = qr.make_image()

        buffer = BytesIO()
        img.save(buffer, format="PNG")

        img_str = base64.b64encode(buffer.getvalue())
        return img_str
    
    def obtener_leyenda_factura(self):
        leyenda = 'Ley Nro 453: Tienes derecho a recibir informacion sobre las caracteristicas y contenidos de los servicios que utilices.'
        if self.sd_leyenda_id:
            leyenda = self.sd_leyenda_id.sd_descripcion_leyenda
        return leyenda

    def get_discount_monto(self, discount, price):
        return (discount * price)/100

    def obtener_leyenda_emision(self):
        if int(self.journal_id.sd_factura_online_id.sd_tipo_emision) == 1 and not self.sd_es_cafc:
            leyenda = 'Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea'
        else:
            leyenda = 'Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido fuera de linea, verifique su envio con su proveedor o \n en la página web www.impuestos.gob.bo'
        return leyenda

    def numero_documento_completo(self):
        if self.partner_id.sd_extension:
            nro = str(self.sd_nro_documento_facturado)+'-'+str(self.partner_id.sd_extension)
        else:
            nro = str(self.sd_nro_documento_facturado)
        return nro
    
    def obtener_fecha_emision(self, fecha):
        fecha_str = ''
        if self.journal_id.fcb_es_electronico:
            # print('fecha reporte',self.sd_fecha_emision)
            fecha_backend = fecha - timedelta(hours=4)
            fecha_str = fecha_backend.strftime('%d/%m/%Y')
            # fecha_str = fecha_backend
            # print('fecha_str',fecha_str)
        return fecha_str

    def obtener_hora_emision(self, fecha):
        hora_str = ''
        if self.journal_id.fcb_es_electronico:
            fecha_backend = fecha - timedelta(hours=4)
            hora_str = fecha_backend.strftime('%I:%M')
            hora_str = hora_str + self.obtener_meridem(fecha_backend)
        return hora_str
    def obtener_meridem(self,fecha):
        '''
        funcion que retorna am y pm
        :param fecha: fecha datatime
        :return: 'AM' o 'PM'
        '''
        hora_emision = fecha.strftime('%H')
        if int(hora_emision) > 11:
            meridem = ' PM'
        else:
            meridem = ' AM'
        return meridem

    def get_sub_total(self):
        sub_total = 0
        for line in self.invoice_line_ids:
            precio_unitario = round(line.price_unit,2)
            descuento = (line.quantity * precio_unitario * line.discount) / 100
            sub_total += (line.quantity * precio_unitario) - descuento
        return sub_total

    def get_titulo_documento(self):
        '''
            funcion que retorna el titulo del la factura segun documento sector
            :return: 'FACTURA' o 'FACTURA TASA CERO - TRANSPORTE DE CARGA INTERNACIONAL'
            dependiendo del sector
        '''
        if self.journal_id.sd_factura_online_id.sd_codigo_documento_sector:
            titulo = 'FACTURA'
            if self.es_debito_credito():
                titulo = 'NOTA CRÉDITO - DÉBITO'
            elif self.sd_codigo_documento_sector == '8':
                titulo = 'FACTURA TASA CERO - VENTA DE LIBROS'
            return titulo

    def get_tipo_factura(self):
        '''
            funcion que retorna el tipo de factura fiscal
            :return: dependiento del tipo de factura "FACTURA SIN DERECHO A CREDITO FISCAL"
        '''
        factura = self.journal_id.sd_factura_online_id.sd_tipo_factura
        factura_id = self.env['tipo.factura.siat'].search([('sd_codigo_clasificador','=',int(factura))])
        return '('+factura_id.sd_descripcion+')'

    def get_report_height(self, paperformat_record_id):
        obj = self.env.ref('sd_facturacion_en_linea_correo_v13.' + paperformat_record_id)
        # print('funciono: ', obj)
        obj.update({'page_height': 220 + (17 * len(self.invoice_line_ids)),
                    'page_width': 80,
                    'margin_top': 10.00,
                    'margin_bottom': 5.00})

    def get_razon_social(self):
        res = self.sd_nombre_facturado if self.sd_nombre_facturado else self.partner_id.name
        return res
