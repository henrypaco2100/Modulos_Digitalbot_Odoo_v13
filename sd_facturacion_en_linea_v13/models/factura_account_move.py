from odoo import api, fields, models, _
import traceback
from datetime import datetime, timedelta
from pysiat.invoices.CompraVentaElectronica import CompraVentaElectronica
from pysiat.invoices.CompraVenta import CompraVenta
from pysiat.invoices.siatinvoice import SiatInvoice
from pysiat.invoices.invoicedetail import InvoiceDetail
from pysiat.invoices.invoicedetailAlquiler import InvoiceDetailAlquiler
from pysiat.invoices.invoicedetailComercialExportacion import InvoiceDetailComercialExportacion
from pysiat.invoices.invoicedetailAlcanzadaIce import InvoiceDetailAlcanzadaIce
from pysiat.invoices.invoicedetailDebitoCredito import InvoiceDetailDebitoCredito
from pysiat.services.service_facturacion_computarizada import ServiceFacturacionComputarizada
from pysiat.services.service_facturacion_electronica import ServiceFacturacionElectronica
from pysiat.classes.siat_exception import SiatException
import pysiat.functions as functions
from pysiat.services.service_sincronizacion import ServiceSincronizacion
from pysiat.services.service_operaciones import ServiceOperaciones
from pysiat.services.service_facturacion import ServiceFacturacion
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import pysiat.constants as constants
import random
sd_contador_leyenda = 1
class FacturaAccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def get_selection_field(self, modelo):
        docs = self.env[modelo].sudo().search([])
        res = []
        for doc in docs:
            res.append((str(doc.sd_codigo_clasificador), str(doc.sd_descripcion)))
        return res
    sd_fecha_emision = fields.Datetime(string='Fecha Emision', copy=False)
    sd_url_factura = fields.Char(string='Link de factura', copy=False)
    sd_cuf = fields.Text(string='CUF', copy=False)
    sd_factura_xml = fields.Binary(string='Factura formato XML')
    sd_razon_social = fields.Char(related='partner_id.st_nombre_compania_facturar', readonly=False)
    sd_nro_documento = fields.Char(related='partner_id.vat', readonly=False)
    sd_codigo_tipo_documento = fields.Selection(related='partner_id.sd_codigo_tipo_documento', readonly=False)
    sd_email = fields.Char(related='partner_id.email', readonly=False)
    sd_nombre_facturado = fields.Char('Nombre Facturado', copy=False)
    sd_email_facturado = fields.Char('Email Facturado', copy=False)
    sd_tipo_documento_facturado = fields.Selection(selection=lambda self: self.get_selection_field('documento.identidad.siat'), string='Tipo Documento Facturado', copy=False)
    sd_nro_documento_facturado = fields.Char('NIT/CI/CEX Facturado', copy=False)
    sd_extension = fields.Char('Complemento Facturado', copy=False)
    #caso especial--------------------------------
    @api.depends('sd_caso_especial')
    def _computed_nit_caso_especial(self):
        for account_move in self:
            es_especial = False
            if account_move.state == 'draft':
                if not account_move.sd_caso_especial == '0' and account_move.sd_es_especial:
                    if account_move.partner_id:
                        es_especial = True
                        nombre_metodo = 'caso_especial_' + str(account_move.sd_caso_especial)
                        ejecutar = getattr(account_move, nombre_metodo, lambda: 'Caso especial inexistente')
                        ejecutar()

            if not es_especial:
                account_move.update({
                    'sd_nit_especial': '0',
                })


    sd_nit_especial = fields.Char('Número de NIT/CI', default='0',store=False, compute='_computed_nit_caso_especial', copy=False)
    sd_razon_social_especial = fields.Char('Razón Social', copy=False)
    sd_razon_social_extranjero = fields.Char('Razón Social Extranjero No Inscrito', copy=False)
    sd_correo_especial = fields.Char('Correo Electrónico (opcional)',copy=False)
    sd_caso_especial = fields.Selection([('0', 'Ninguna'),
                                         ('1', '99001-Extranjero no Inscrito'),
                                         ('2', '99002-Control Tributario'),
                                         ('3', '99003-Ventas Menores')],
                                        string='Caso especial',
                                        default='0', copy=False)

    sd_es_especial = fields.Boolean(related='partner_id.sd_es_caso_especial', copy=False)
    #-------------------------------------------------------------------------------
    sd_sia_emision_paquete_id = fields.Many2one('siat.emision.paquete.offline', string='Siat Emisión de Paquete')
    # sd_paquete_wizard_id = fields.Many2one('wizard.paquete.factura', string='wizard Emisión de Paquete')
    sd_siat_emision_masiva_id = fields.Many2one('siat.emision.masiva', string='Siat Emisión Masiva')
    sd_motivo_id = fields.Many2one('motivo.anulacion.siat', string='Motivo', group='sd_facturacion_en_linea_v13.sd_anulacion_factura_group')
    sd_codigo_descripcion = fields.Char('Código descripción', copy=False)
    sd_codigo_recepcion = fields.Char('Código Recepción', copy=False)
    sd_es_test = fields.Boolean(string='Es test', default=False, copy=False)
    sd_nro_factura_siat = fields.Integer('No. Factura', copy=False, group_operator=False)
    sd_nro_debito_credito = fields.Integer('No. Debito-Credito', copy=False)
    sd_factura_original = fields.Many2one('account.move', string='Factura Original', domain="[('type','=','out_invoice')]")

    @api.model
    def _get_default_metodo_pago(self):
        metodo_efectivo = self.env['ir.model.data'].xmlid_to_res_id("sd_facturacion_en_linea_v13.sd_data_metodo_pago_default")
        # print(metodo_efectivo, 'metodo efectivo')
        return metodo_efectivo
    sd_metodo_pago = fields.Many2one('metodo.pago.siat', string='Método Pago',default=lambda self: self._get_default_metodo_pago(), domain="[('sd_activo','=',True)]")
    sd_codigo_clasificador_mp = fields.Integer(related='sd_metodo_pago.sd_codigo_clasificador')
    # sd_numero_tarjeta = fields.Integer(string='Número de tarjeta')
    sd_nro_tarjeta = fields.Char(string='Número de tarjeta')
    sd_descuento_adicional = fields.Float(string='Descuento Adicional')
    sd_codigo_excepcion = fields.Integer(string='Código excepcion', help='Se envia para autorizar el registro  de una factura con NIT inválido. 0=None, 1=autorizado', default=1, copy=False)
    sd_cantidad_gift_card = fields.Float(string='Monto Gift-Card', copy=False)
    sd_monto_total_sujeto_iva = fields.Float('Monto Total Sujeto a Iva', copy=False)
    sd_monto_descuento = fields.Float('Monto descuento', copy=False)
    sd_monto_total_moneda = fields.Float('Monto Total Moneda', copy=False)
    sd_es_giftcard = fields.Boolean('Es Gift-Card', default=False)
    sd_es_tarjeta = fields.Boolean('Es Tarjeta', default=False)
    #factura en linea
    sd_es_online = fields.Boolean(related='journal_id.fcb_es_electronico')
    sd_is_offline = fields.Boolean('Fuera de linea', default=False, copy=False)
    sd_cambiar_endpoint = fields.Boolean('Cambiar EndPoint', related='journal_id.sd_factura_online_id.sd_cambiar_endpoint')
    sd_cufd_paquete = fields.Char('Cufd Factura')
    sd_leyenda_id = fields.Many2one('leyenda.factura.siat', string='Leyenda Factura')
    sd_estado_siat = fields.Selection([('valida', 'VALIDA'),
                                       ('anulada', 'ANULADA'),
                                       ('sin_publicar', 'NO VALIDADA')], string='Estado Siat',
                                      default='sin_publicar')
    #------------------------------------------------------
    # envio paquete con cafc
    sd_es_cafc = fields.Boolean(string='Tiene Cafc', default=False)
    sd_nro_cafc = fields.Integer('Número de Cafc')
    sd_codigo_cafc = fields.Char(string='Codigo Cafc')
    # ---------------------Campos extras para faturas completas------------------------
    sd_codigo_documento_sector = fields.Selection(related='journal_id.sd_documento_sector_siat')
    # ------ factura de alquiler ------------
    sd_periodo_facturado = fields.Char(string='Periodo Facturado', store=False, compute='_computed_periodo_facturado',
                                       copy=False)
    sd_periodo_inicio = fields.Date(string='Periodo Inicio')
    sd_periodo_fin = fields.Date(string='Periodo Fin')

    # ------ factura ----------------

    #--------Nota debito-Credito---------------
    sd_monto_total_devuelto = fields.Float('Monto Total devuelto', copy=False)
    sd_monto_efectivo_debito_credito = fields.Float('Monto efectivo', copy=False)
    # ..........................
    # move_paquete_id = fields.Many2one('wizard.paquete.factura', 'Componente del factura del wizard',
    #                           index=True, readonly=True, auto_join=True, ondelete="cascade")

    @api.depends('sd_periodo_inicio', 'sd_periodo_fin')
    def _computed_periodo_facturado(self):
        for account_move in self:
            # print('computarizado 2')
            try:
                if account_move.sd_periodo_inicio and account_move.sd_periodo_fin:
                    periodo_ini = account_move.sd_periodo_inicio.strftime('%d DE %B DE %Y').upper()
                    periodo_fin = account_move.sd_periodo_fin.strftime('%d DE %B DE %Y').upper()
                    periodo_fact = periodo_ini + ' AL ' + periodo_fin
                    # account_move.update({
                    #     'sd_periodo_facturado': periodo_fact
                    # })
                    account_move.sd_periodo_facturado = periodo_fact
                else:
                    account_move.sd_periodo_facturado = None
            except ValueError:
                account_move.sd_periodo_facturado = None

    @api.onchange('sd_nro_tarjeta')
    def control_numero_tarjeta(self):
        # print('control numerico')
        caracteres=self.sd_nro_tarjeta
        diccionario_numerico={'0','1','2','3','4','5','6','7','8','9'}
        if caracteres:
            for i in caracteres:
                if not i in diccionario_numerico:
                    self.sd_nro_tarjeta=''
                    return {
                        'warning': {
                            'message': _(
                                f'Se permiten solo caracteres numérico en el campo:"Número de tarjeta", porfavor vuelva a intentarlo!!. ')
                        }
                    }
            if len(caracteres) != 16:

                return {
                    'warning': {
                        'message': _(
                            f'La cantidad de digitos debe ser igual a 16, porfavor complete los 16 dígitos.')
                    }
                }

    @api.constrains('sd_nro_tarjeta')
    def _check_digits(self):
        for record in self:
            if record.sd_nro_tarjeta and not record.sd_nro_tarjeta.isdigit():
                raise ValidationError("El campo debe contener solo dígitos numéricos.")

    @api.onchange('sd_nro_tarjeta')
    def _onchange_my_field(self):
        for record in self:
            if record.sd_nro_tarjeta and record.sd_nro_tarjeta.isdigit():
                formatted_value = record.sd_nro_tarjeta[:4] + '0' * 8 + record.sd_nro_tarjeta[-4:]
                record.sd_nro_tarjeta = formatted_value

    @api.onchange('sd_metodo_pago')
    def resetear_nro_tarjeta(self):
        self.verificar_metodo_giftcard()
        self.verificar_metodo_tarjeta()



    @api.onchange('sd_correo_especial')
    def actualizar_correo_cliente(self):
        if self.sd_es_especial:
            self.partner_id.update({
                'email': self.sd_correo_especial
            })

    @api.onchange('sd_descuento_adicional')
    def actualizar_descuento_adicional(self):
        if self.sd_descuento_adicional < 0:
            self.update({
                'sd_descuento_adicional': 0.00
            })

    @api.onchange('sd_razon_social_extranjero')
    def actualizar_razon_social_extranjero(self):
        self.partner_id.update({
            'st_nombre_compania_facturar': self.sd_razon_social_extranjero
        })
    def caso_especial_1(self):
        self.update({
            'sd_nit_especial': '99001'
        })
        self.partner_id.update({
            'vat': '99001',
        })

    def caso_especial_2(self):
        self.update({
            'sd_nit_especial': '99002',
            'sd_razon_social_especial': 'CONTROL TRIBUTARIO'
        })
        self.partner_id.update({
            'vat': '99002',
            'st_nombre_compania_facturar': 'CONTROL TRIBUTARIO'
        })

    def caso_especial_3(self):
        self.update({
            'sd_nit_especial': '99003',
            'sd_razon_social_especial': 'VENTAS MENORES DEL DIA'
        })
        self.partner_id.update({
            'vat': '99003',
            'st_nombre_compania_facturar': 'VENTAS MENORES DEL DIA'
        })
    def verificar_metodo_giftcard(self):
        giftcard_ids = self.get_metodo_giftcard_ids()
        # print('metodos:',giftcard_ids)
        if self.sd_metodo_pago.sd_codigo_clasificador in (giftcard for giftcard in giftcard_ids):
            self.sudo().write({
                'sd_es_giftcard': True
            })
        else:
            self.sudo().write({
                'sd_es_giftcard': False,
                'sd_cantidad_gift_card': 0
            })
    def get_metodo_giftcard_ids(self):
        metodos_ids = self.env['metodo.pago.siat'].search([('sd_descripcion', 'ilike', 'gift')])
        if metodos_ids:
            return metodos_ids.mapped('sd_codigo_clasificador')
        else:
            return []

    def verificar_metodo_tarjeta(self):
        metodo_tarjeta_ids = self.get_metodo_tarjeta()
        if self.sd_metodo_pago.sd_codigo_clasificador in (tarjeta for tarjeta in metodo_tarjeta_ids):
            sw = True
        else:
            sw = False
            self.sd_nro_tarjeta = ''
        self.sudo().write({
            'sd_es_tarjeta': sw
        })

    def get_metodo_tarjeta(self):
        metodos_ids = self.env['metodo.pago.siat'].search([('sd_descripcion', 'ilike', 'tarjeta')])
        if metodos_ids:
            return metodos_ids.mapped('sd_codigo_clasificador')
        else:
            return []
    def verificar_obligatorio(self, diario, cliente):
        no_validos = []
        fact = diario.sd_factura_online_id
        if (diario.fcb_es_electronico):
            if not fact.sd_cuis:
                no_validos.append('Codigo cuis')
            if not diario.sd_nit_em:
                no_validos.append('nit emisor')
            if not diario.sd_razon_social:
                no_validos.append('razon social')
            if not diario.sd_municipio:
                no_validos.append('municipio')
            if not diario.fcb_siguiente_Numero:
                no_validos.append('numero de factura')
            if not fact.sd_cufd:
                no_validos.append('cufd')
            if not self.sd_codigo_documento_sector:
                no_validos.append('codigo documento sector')
            if not fact.sd_codigo_sucursal:
                no_validos.append('codigo sucursal')
            if not fact.sd_direccion:
                no_validos.append('direccion')
            # if not self.sd_fecha_emision:
            #     no_validos.append('fecha de emision')
            if not cliente.sd_codigo_tipo_documento:
                no_validos.append('Codigo tipo de documento')
            if not cliente.vat:
                no_validos.append('Numero de documento')
            if not cliente.id:
                no_validos.append('Codigo de cliente')
            if not cliente.st_nombre_compania_facturar:
                no_validos.append('Nombre a facturar')
            if not self.amount_total:
                no_validos.append('monto total')
            if not self.amount_untaxed:
                no_validos.append('monto total sujeto a iva')
            if not self.currency_id.id:
                no_validos.append('codigo de moneda')
            if not self.currency_id.rate:
                no_validos.append('tipo de cambio')
            if not self.sd_metodo_pago:
                no_validos.append('Metodo de pago')
        return no_validos


    def validar_campos_factura(self, campo, tipo):
        if not campo:
            raise UserError(_('El campo "%s" no corresponde verifique sus datos') % (tipo))
        else:
            return campo

    def validar_producto_sin(self, productos):
        productos_str=''
        unidad_str=''
        for producto in productos:
            if not producto.product_id.sd_codigo_product_id.sd_codigo_producto:
                productos_str = productos_str + producto.name + '\n'
            if not producto.product_uom_id.sd_unidad_medida_id and not producto.product_id.sd_unidad_medida_id:
                unidad_str = unidad_str + producto.name + '\n'
        if productos_str != '' or unidad_str != '':
            if productos_str == '':
                msg_prod = 'Verifique la unidad de medida siat de los siguientes productos: \n' + unidad_str
            elif unidad_str == '':
                msg_prod = 'Verifique el producto sin de los siguientes productos: \n' + productos_str
            else:
                msg_prod = 'Verifique el producto sin de los siguientes productos: \n' + productos_str + '\n' + \
                           'Verifique la unidad de medida siat de los siguientes productos: \n' + unidad_str
            raise UserError(_(msg_prod))

    def construir_factura(self, modalidad,esBot=None, esPaquete=None, test=None):
        fact = self.journal_id.sd_factura_online_id
        self.get_fecha_emision(esBot=esBot, test=test, esPaquete=esPaquete)
        # print('fecha-emision', self.sd_fecha_emision)
        nro_factura = self.sd_nro_factura_siat if self.state == 'posted' else self.journal_id.fcb_siguiente_Numero
        nro_debito_credito = self.journal_id.sd_siguiente_numero_debito_credito
        if self.sd_es_cafc:
            nro_factura = self.sd_nro_cafc
        cfg = fact.getConfig(fact.sd_codigo_modalidad, fact.sd_codigo_ambiente, fact.sd_codigo_sistema, fact.sd_nombre_sistema, fact.sd_nit_em,  fact.sd_nombre_company, fact.sd_tipo_sistema, fact.sd_token)
        fecha_emision = self.sd_fecha_emision
        # print('fecha de la factura frontend',fecha_emision)
        factura = None
        if int(modalidad) == constants.MOD_ELECTRONICA_ENLINEA:
            factura = CompraVentaElectronica(self.sd_codigo_documento_sector if not self.es_debito_credito() else '24')
        else:
            factura = CompraVenta(self.sd_codigo_documento_sector if not self.es_debito_credito() else '24')

        subtotal = 0
        tipo_cambio = self.currency_id.rate
        self.validar_producto_sin(self.invoice_line_ids)
        self.verificar_metodo_tarjeta()
        if self.sd_factura_original and self.type == 'out_refund':
            for line_origin in self.sd_factura_original.invoice_line_ids:
                detalle = self.obtener_detalle_factura(self.sd_codigo_documento_sector)
                detalle.cantidad = round(self.validar_campos_factura(line_origin.quantity, 'cantidad'), 2)
                # print('Cantidad:', str(type(detalle.cantidad))+' '+str(detalle.cantidad))
                detalle.actividadEconomica = self.validar_campos_factura(
                    line_origin.product_id.sd_codigo_product_id.sd_codigo_actividad.sd_codigo_caeb, 'actividad')
                # print('Actividad', str(type(detalle.actividadEconomica))+' '+str(detalle.actividadEconomica))
                detalle.codigoProducto = self.validar_campos_factura(
                    line_origin.product_id.default_code or str(line_origin.product_id.id), 'codigo Producto')
                # print('codigo Producto:', str(type(detalle.codigoProducto))+' '+str(detalle.codigoProducto))
                detalle.codigoProductoSin = int(line_origin.product_id.sd_codigo_product_id.sd_codigo_producto)
                # print('Producto sin', str(type(detalle.codigoProductoSin))+' '+str(detalle.codigoProductoSin))
                detalle.descripcion = self.validar_campos_factura(line_origin.name, 'nombre de producto')
                # print('descripcion', str(type(detalle.descripcion))+' '+str(detalle.descripcion))
                detalle.precioUnitario = round(
                    (self.validar_campos_factura(line_origin.price_unit, 'precio unitario')) / tipo_cambio, 2)
                # print('precio Unitaria', str(type(line.price_unit))+' '+str(line.price_unit))
                detalle.montoDescuento = round((line_origin.discount * (detalle.precioUnitario * line_origin.quantity)) / 100, 2)
                # print('monto descuento', str(type(detalle.montgetConfigoDescuento))+' '+str(detalle.montoDescuento))
                detalle.subTotal = round((detalle.precioUnitario * line_origin.quantity - detalle.montoDescuento), 2)
                # print('subtotal:', str(type(detalle.subTotal))+' '+str(detalle.subTotal))
                detalle.unidadMedida = int(line_origin.product_uom_id.sd_unidad_medida_id.sd_codigo_clasificador or line_origin.product_id.sd_unidad_medida_id.sd_codigo_clasificador)
                if self.es_debito_credito():
                    detalle.codigoDetalleTransaccion = 1
                factura.detalle.append(detalle)

        for line in self.invoice_line_ids:
            detalle = self.obtener_detalle_factura(self.sd_codigo_documento_sector)
            detalle.cantidad = round(self.validar_campos_factura(line.quantity, 'cantidad'), 2)
            # print('Cantidad:', str(type(detalle.cantidad))+' '+str(detalle.cantidad))
            detalle.actividadEconomica = self.validar_campos_factura(line.product_id.sd_codigo_product_id.sd_codigo_actividad.sd_codigo_caeb, 'actividad')
            # print('Actividad', str(type(detalle.actividadEconomica))+' '+str(detalle.actividadEconomica))
            detalle.codigoProducto = self.validar_campos_factura(line.product_id.default_code or str(line.product_id.id), 'codigo Producto')
            # print('codigo Producto:', str(type(detalle.codigoProducto))+' '+str(detalle.codigoProducto))
            detalle.codigoProductoSin = int(line.product_id.sd_codigo_product_id.sd_codigo_producto)
            # print('Producto sin', str(type(detalle.codigoProductoSin))+' '+str(detalle.codigoProductoSin))
            detalle.descripcion = self.validar_campos_factura(line.name, 'nombre de producto')
            # print('descripcion', str(type(detalle.descripcion))+' '+str(detalle.descripcion))
            detalle.precioUnitario = round((self.validar_campos_factura(line.price_unit, 'precio unitario'))/tipo_cambio, 2)
            # print('precio Unitaria', str(type(line.price_unit))+' '+str(line.price_unit))
            detalle.montoDescuento = round((line.discount * (detalle.precioUnitario * line.quantity))/100, 2)
            # print('monto descuento', str(type(detalle.montgetConfigoDescuento))+' '+str(detalle.montoDescuento))
            detalle.subTotal = round((detalle.precioUnitario * line.quantity - detalle.montoDescuento), 2)
            # print('subtotal:', str(type(detalle.subTotal))+' '+str(detalle.subTotal))
            detalle.unidadMedida = int(line.product_id.sd_unidad_medida_id.sd_codigo_clasificador)
            if self.es_debito_credito():
                detalle.codigoDetalleTransaccion = 2
            factura.detalle.append(detalle)

            subtotal += detalle.subTotal
            # monto_gift_card += line.sd_monto_gift_card

        factura.cabecera.razonSocialEmisor = cfg['razonSocial']
        # print('razon social:', str(type(factura.cabecera.razonSocialEmisor))+' '+str(factura.cabecera.razonSocialEmisor))
        factura.cabecera.municipio = fact.sd_municipio
        # print('municipio:', str(type(factura.cabecera.municipio))+' '+str(factura.cabecera.municipio))
        factura.cabecera.telefono = fact.sd_nro_company
        # print('telefono', str(type(factura.cabecera.telefono))+' '+str(factura.cabecera.telefono))
        factura.cabecera.numeroFactura = self.sd_factura_original.sd_nro_factura_siat if self.es_debito_credito() else nro_factura
        # print('nroFactura', str(type(factura.cabecera.numeroFactura))+' '+str(factura.cabecera.numeroFactura))
        factura.cabecera.codigoSucursal = int(fact.sd_codigo_sucursal)
        # print('codigo sucursal:', str(type(factura.cabecera.codigoSucursal))+' '+str(factura.cabecera.codigoSucursal))
        factura.cabecera.direccion = fact.sd_direccion
        # print('direccion:', str(type(factura.cabecera.direccion))+' '+str(factura.cabecera.direccion))
        factura.cabecera.codigoPuntoVenta = fact.sd_codigo_punto_venta.sd_codigo_punto_venta if fact.sd_es_punto_venta else 0
        # print('codigo PV', str(type(factura.cabecera.codigoPuntoVenta))+' '+str(factura.cabecera.codigoPuntoVenta))
        # if not esPaquete or esBot:
        factura.cabecera.fechaEmision = functions.sb_siat_format_datetime(fact.obtener_fecha_backend(fecha_emision))
        # print('fechaEmision:', str(type(factura.cabecera.fechaEmision))+' '+str(factura.cabecera.fechaEmision))
        factura.cabecera.nombreRazonSocial = self.partner_id.st_nombre_compania_facturar if self.partner_id.st_nombre_compania_facturar else self.partner_id.name
        # print('cliente:', str(type(factura.cabecera.nombreRazonSocial))+' '+str(factura.cabecera.nombreRazonSocial))
        factura.cabecera.codigoTipoDocumentoIdentidad = int(self.partner_id.sd_codigo_tipo_documento)
        # print('codido CI:', str(type(factura.cabecera.codigoTipoDocumentoIdentidad))+' ', str(factura.cabecera.codigoTipoDocumentoIdentidad))
        factura.cabecera.numeroDocumento = self.partner_id.vat if self.partner_id.vat != '0' else self.partner_id.id
        # print('nro CI:', str(type(factura.cabecera.numeroDocumento))+' '+str(factura.cabecera.numeroDocumento))
        factura.cabecera.complemento = self.get_no_obligatorio(self.partner_id.sd_extension) if int(self.sd_codigo_tipo_documento) == 1 else None
        # print('complemento:', str(type(factura.cabecera.complemento))+' '+str(factura.cabecera.complemento))
        factura.cabecera.codigoCliente = str(self.partner_id.id)
        # print('codigoCliente', str(type(factura.cabecera.codigoCliente))+' '+str(factura.cabecera.codigoCliente))
        if int(self.sd_codigo_documento_sector) == constants.TiposDocumentoSector.FACTURA_ALQUILER_INMUEBLES:
            factura.cabecera.periodoFacturado = self.sd_periodo_facturado
        if not int(self.sd_codigo_documento_sector) == constants.TiposDocumentoSector.FACTURA_ALQUILER_INMUEBLES \
                and not self.es_debito_credito():
            factura.cabecera.montoGiftCard = round((self.sd_cantidad_gift_card if self.sd_es_giftcard else 0) / tipo_cambio, 2)
            # print('monto gift card:', str(type(factura.cabecera.montoGiftCard))+' '+str(factura.cabecera.montoGiftCard))
        if not self.es_debito_credito():
            factura.cabecera.codigoMetodoPago = self.sd_metodo_pago.sd_codigo_clasificador
            # print('codigo Met. Pago:', str(type(factura.cabecera.codigoMetodoPago))+' '+str(factura.cabecera.codigoMetodoPago))
            factura.cabecera.numeroTarjeta = (self.get_no_obligatorio(self.sd_nro_tarjeta) or self.partner_id.sd_nro_tarjeta) if self.sd_es_tarjeta else None
            # print('nro Tarjeta:', str(type(factura.cabecera.numeroTarjeta))+' '+str(factura.cabecera.numeroTarjeta))
            factura.cabecera.montoTotal = round(subtotal - (self.sd_descuento_adicional / tipo_cambio), 2)
            # print('monto total:', str(type(factura.cabecera.montoTotal))+' '+str(factura.cabecera.montoTotal))
            factura.cabecera.montoTotalSujetoIva = self.obtener_monto_total_iva(factura.cabecera.montoTotal,
                                                                                factura.cabecera.montoGiftCard)
            # print('monto total iva:', str(type(factura.cabecera.montoTotalSujetoIva))+' '+str(factura.cabecera.montoTotalSujetoIva))
            factura.cabecera.descuentoAdicional = round(self.sd_descuento_adicional / tipo_cambio, 2)
            # print('descuento adicional:', str(type(factura.cabecera.descuentoAdicional))+' '+str(factura.cabecera.descuentoAdicional))
            factura.cabecera.codigoMoneda = self.currency_id.sd_tipo_moneda.sd_codigo_clasificador
            # print('codigo Moneda', str(type(factura.cabecera.codigoMoneda))+' '+str(factura.cabecera.codigoMoneda))
            factura.cabecera.tipoCambio = round((1 / tipo_cambio), 2)
            # print('tipo cambio', str(type(factura.cabecera.tipoCambio))+' '+str(factura.cabecera.tipoCambio))
            factura.cabecera.montoTotalMoneda = round(factura.cabecera.montoTotal / factura.cabecera.tipoCambio, 2)
            factura.cabecera.cafc = self.get_no_obligatorio(self.sd_codigo_cafc)
        if self.es_debito_credito():
            factura.cabecera.numeroAutorizacionCuf = self.sd_factura_original.sd_cuf
            factura.cabecera.fechaEmisionFactura = functions.sb_siat_format_datetime(fact.obtener_fecha_backend(self.sd_factura_original.sd_fecha_emision))
            factura.cabecera.montoTotalOriginal = self.sd_factura_original.sd_monto_total_sujeto_iva + self.sd_factura_original.sd_cantidad_gift_card + self.sd_factura_original.sd_descuento_adicional
            factura.cabecera.montoTotalDevuelto = round(subtotal - (self.sd_descuento_adicional / tipo_cambio), 2)
            factura.cabecera.montoDescuentoCreditoDebito = self.sd_factura_original.sd_descuento_adicional
            factura.cabecera.montoEfectivoCreditoDebito = round((factura.cabecera.montoTotalDevuelto * 0.13)/ tipo_cambio, 2)
            factura.cabecera.numeroNotaCreditoDebito = nro_debito_credito
            # print('numero de debito:',factura.cabecera.numeroNotaCreditoDebito)

        factura.cabecera.codigoExcepcion = self.get_no_obligatorio(self.sd_codigo_excepcion)
        # print('monto Total moneda', str(type(factura.cabecera.montoTotalMoneda))+' '+str(factura.cabecera.montoTotalMoneda))
        factura.cabecera.usuario = self.env.user.name

        # print('usuario', str(type(factura.cabecera.usuario))+' '+str(factura.cabecera.usuario))
        # factura.cabecera.codigoDocumentoSector = int(fact.sd_codigo_documento_sector)
        # verificar que no se cambie la leyenda cuando la factura fue publicada offline o con cafc
        factura.cabecera.leyenda = self.leyenda_aleatoria()
        if not esBot and not self.sd_es_cafc:
            if self.type != 'out_refund':
                self.journal_id.siguiente_numero_facturacion()
            else:
                self.journal_id.siguiente_numero_debito_credito()

        return factura

    def obtener_detalle_factura(self, docSector):
        resdetalle = InvoiceDetail()
        if self.es_debito_credito():
            resdetalle = InvoiceDetailDebitoCredito()
        else:
            if int(docSector) == constants.TiposDocumentoSector.FACTURA_COMERCIAL_EXPORTACION:
                resdetalle = InvoiceDetailComercialExportacion()
            elif int(docSector) == constants.TiposDocumentoSector.FACTURA_PRODS_ICE:
                resdetalle = InvoiceDetailAlcanzadaIce()
            elif int(docSector) in (constants.TiposDocumentoSector.FACTURA_ALQUILER_INMUEBLES,
                                    constants.TiposDocumentoSector.FACTURA_TASA_CERO_LIBROS):
                resdetalle = InvoiceDetailAlquiler()

        return resdetalle

    def leyenda_aleatoria(self):
        if not self.sd_leyenda_id:
            leyendas = self.env['leyenda.factura.siat'].search([])
            contador_leyenda = 1
            turno_leyenda = self.journal_id.sd_contador_leyenda
            for leyenda in leyendas:
                if contador_leyenda == turno_leyenda:
                    if len(leyendas) == turno_leyenda:
                        self.journal_id.update({
                            'sd_contador_leyenda': 1
                        })
                    else:
                        self.journal_id.update({
                            'sd_contador_leyenda': turno_leyenda+1
                        })
                    self.journal_id.write({
                        'sd_siguiente_leyenda_id': self.siguiente_leyenda(self.journal_id.sd_contador_leyenda)
                    })
                    self.update({'sd_leyenda_id': leyenda.id})
                    return leyenda.sd_descripcion_leyenda
                contador_leyenda += 1
        else:
            return self.sd_leyenda_id.sd_descripcion_leyenda

    def obtener_monto_total_iva(self, monto_total, monto_gift_card):
        if int(self.sd_codigo_documento_sector) != constants.TiposDocumentoSector.FACTURA_TASA_CERO_LIBROS:
            return round(monto_total - (monto_gift_card if self.sd_es_giftcard else 0), 2)
        else:
            return 0

    def siguiente_leyenda(self, turno_siguiente_leyenda):
        leyendas = self.env['leyenda.factura.siat'].search([])
        contador_leyenda = 1
        for leyenda in leyendas:
            if contador_leyenda == turno_siguiente_leyenda:
                return leyenda.id
            contador_leyenda += 1
        
    def ocultar_numeros_tarjeta(self, nro_tarjeta):
        if nro_tarjeta:
            cadena_nro_tarjeta = str(nro_tarjeta)
            cadena_nro_tarjeta = cadena_nro_tarjeta[0:3]+'00000000'+cadena_nro_tarjeta[12:]
            return int(cadena_nro_tarjeta)
        else:
            return None
    def get_no_obligatorio(self, campo):
        if campo:
            return campo
        else:
            return None
    def get_fecha_emision(self, esBot=None, test=None, esPaquete=None):
        fact_online = self.journal_id.sd_factura_online_id
        # if test:
        #     self.write({
        #         # 'sd_fecha_emision': datetime.now() - timedelta(hours=4)
        #         'sd_fecha_emision': test
        #     })
        # else:
        #     self.write({
        #         'sd_fecha_emision': self.sd_fecha_emision if self.sd_fecha_emision else datetime.now()
        #     })
        if not esBot and not self.sd_es_cafc and not fact_online.sd_es_test and not esPaquete:
            self.write({
                # 'sd_fecha_emision': datetime.now() - timedelta(hours=4)
                'sd_fecha_emision': datetime.now()
            })
        elif fact_online.sd_es_test:
            self.write({
                'sd_fecha_emision': fact_online.sd_evento_significativo_id.sd_fecha_inicio or datetime.now()
            })

    def es_debito_credito(self):
        return self.type == 'out_refund'

    def post(self, esMasiva=None):
        vals = super(FacturaAccountMove, self).post()
        for move in self:
            # if move.type == 'out_refund' and not self.es_debito_credito():
            #     codigo_doc_sector_anterior = move.journal_id.sd_factura_online_id.sd_codigo_documento_sector
            #     tipo_factura = move.journal_id.sd_factura_online_id.sd_tipo_factura
            #     move.journal_id.sd_factura_online_id.update({'sd_codigo_documento_sector': '24',
            #                                                  'sd_tipo_factura': '3'})

            if move.type == 'out_invoice' or move.type == 'out_refund' and move.sd_estado_siat == 'sin_publicar':
                if move.journal_id.fcb_es_electronico:
                    move.get_documento_sector()
                    if move.journal_id.sd_factura_online_id.verificar_grupo_admin() or \
                            move.journal_id.sd_factura_online_id.verificar_grupo_user():
                        if int(move.journal_id.sd_factura_online_id.sd_tipo_emision) == 1 and not esMasiva:
                            res_publicado = move.verificar_estado_factura_siat()
                        else:
                            res_publicado = None
                        # res_publicado = None
                        if not res_publicado:
                            res_publicado = {}
                            res_publicado['codigoDescripcion'] = 'RECHAZADA'
                        if res_publicado['codigoDescripcion'] == 'RECHAZADA' or not move.sd_cuf:
                            if not move.sd_codigo_recepcion:
                                diario = move.journal_id
                                fact_online = diario.sd_factura_online_id
                                if not fact_online.existe_cuis():
                                    fact_online.solicitudCuis()
                                if not fact_online.existe_cufd():
                                    fact_online.solicitudCufd()
                                    if not fact_online.sd_cufd:
                                        raise UserError(_('Cufd no valido no se puede continuar con la publicacion. \n Por favor comuniquese con su soporte.'))
                                cufd = fact_online.sd_cufd_ids.obtener_vigente()
                                cliente = move.partner_id
                                res_verificacion = move.verificar_obligatorio(diario, cliente)
                                if not res_verificacion:
                                    move.verificar_monto_linea_adicional()
                                    move.verificar_monto_giftcard()
                                    # cfg = fact_online.getConfig(fact_online.sd_codigo_modalidad, fact_online.sd_codigo_ambiente, fact_online.sd_codigo_sistema,
                                    #                             fact_online.sd_nombre_sistema, fact_online.sd_nit_em,
                                    #                             fact_online.company_id.name, fact_online.sd_tipo_sistema, fact_online.sd_token)
                                    # service = ServiceFacturacionComputarizada()
                                    # service.setConfig(cfg)
                                    # service.cuis = fact_online.sd_cuis
                                    # service.cufd = fact_online.sd_cufd
                                    if move.sd_es_cafc:
                                        cufd_evento = move.get_cufd_evento()
                                        # print('cufd desde la funcion',cufd_evento)
                                        codigo_control_dinamico = cufd_evento.sd_codigo_control
                                        nro_factura_siat_dinamico = move.sd_nro_cafc
                                    else:
                                        codigo_control_dinamico = fact_online.sd_codigo_control
                                        nro_factura_siat_dinamico = move.journal_id.fcb_siguiente_Numero
                                    # service.codigoControl = codigo_control_dinamico
                                    # service.codigoControl = fact_online.sd_codigo_control
                                    # ---------------------------- testear cufd paquete
                                    move.write({
                                        'sd_nro_factura_siat': nro_factura_siat_dinamico,
                                        'sd_cufd_paquete': fact_online.sd_cufd
                                    })
                                    move.verificar_nit_valido(not_return=True)
                                    # print('antes de construir factura', move.state, move.name)
                                    factura = move.construir_factura(fact_online.sd_codigo_modalidad)
                                    if move.sd_cambiar_endpoint:#quitar or fact_online.sd_tipo_emision == '2'
                                        if fact_online.sd_tipo_emision == '2':
                                            move.write({
                                                'sd_is_offline': True
                                            })
                                        else:
                                            move.write({
                                                'sd_is_offline': True
                                            })
                                            fact_online.write({
                                                'sd_tipo_emision': '2'
                                            })
                                            evento_id = move.create_evento_significativo(self.sd_fecha_emision)
                                            fact_online.write({
                                                'sd_evento_id': evento_id.id
                                            })
                                            fact_online.encender_bot()

                                    # move.verificar_nit_valido(not_return=True)
                                    # factura = move.construir_factura(fact_online.sd_codigo_modalidad)
                                    tipo_emision_ambos_casos = constants.TIPO_EMISION_OFFLINE if move.sd_es_cafc else fact_online.sd_tipo_emision
                                    # solicitud de factura
                                    # print(move.sd_es_cafc)
                                    res, facturaXml = self.publicar_factura_siat(fact_online,codigo_control_dinamico,factura,tipo_emision_ambos_casos)
                                    # print(res)
                                    if res:
                                        if res['codigoDescripcion'] == 'VALIDADA'or res['codigoDescripcion'] == 'OFFLINE' or move.sd_is_offline or move.sd_es_cafc or fact_online.sd_es_test:
                                            # print('RESPONSE RECEPCION', res)
                                            # print('FACTURA CUF:', factura.cabecera.cuf)
                                            dominio ='siat.impuestos.gob.bo' if move.journal_id.sd_factura_online_id.sd_codigo_ambiente == '1' else 'pilotosiat.impuestos.gob.bo'
                                            url = 'https://'+dominio+'/consulta/QR?nit={0}&cuf={1}&numero={2}&t=2'.format(
                                                fact_online.sd_nit_em,
                                                factura.cabecera.cuf,
                                                factura.cabecera.numeroFactura
                                            ) if not move.es_debito_credito() else 'https://'+dominio+'/consulta/QR?nit={0}&cuf={1}&numero={2}&t=2'.format(
                                                fact_online.sd_nit_em,
                                                factura.cabecera.cuf,
                                                factura.cabecera.numeroNotaCreditoDebito
                                            )
                                            print('SIAT URL: ', url)

                                            move.write({
                                                'sd_cuf': factura.cabecera.cuf,
                                                'sd_url_factura': url,
                                                'sd_monto_total_sujeto_iva': factura.cabecera.montoTotal-factura.cabecera.montoGiftCard if not self.es_debito_credito() else factura.cabecera.montoTotalDevuelto,
                                                'sd_monto_total_moneda': factura.cabecera.montoTotalMoneda if not self.es_debito_credito() else factura.cabecera.montoTotalDevuelto,
                                                'sd_nombre_facturado': self.sd_razon_social,
                                                'sd_tipo_documento_facturado': self.sd_codigo_tipo_documento,
                                                'sd_nro_documento_facturado': self.sd_nro_documento,
                                                'sd_extension': self.partner_id.sd_extension,
                                                'sd_nro_debito_credito': self.journal_id.sd_siguiente_numero_debito_credito,
                                                'sd_codigo_documento_sector': '24' if self.es_debito_credito() else self.sd_codigo_documento_sector,
                                                'sd_monto_total_devuelto': factura.cabecera.montoTotalDevuelto if self.es_debito_credito() else 0,
                                                'sd_monto_efectivo_debito_credito': factura.cabecera.montoEfectivoCreditoDebito if self.es_debito_credito() else 0
                                            })
                                            # if move.type == 'out_refund' and self.es_debito_credito():
                                            #     move.journal_id.sd_factura_online_id.update({'sd_codigo_documento_sector': codigo_doc_sector_anterior,
                                            #                                                  'sd_tipo_factura': tipo_factura})
                                            self.clean_cliente()
                                            move.calcular_totales_factura(factura)
                                            if fact_online.existe_cufd():
                                                contador = cufd.sd_contador_factura + 1
                                                cufd.write({
                                                    'sd_contador_factura': contador
                                                })
                                            if not move.sd_es_test:

                                                move.sudo().action_imprimir_factura_enviar_correo_siat(facturaXml=facturaXml, es_pos=True)
                                                mjs = fact_online.mensaje_personalizador('Se publico correctamente la factura.')
                                                return mjs
                                        else:
                                            mensajes = ''
                                            if not res['codigoDescripcion'] =='OFFLINE':
                                                for mensaje in res['mensajesList']:
                                                    mensajes = mensajes + mensaje['descripcion'] +'\n'
                                                raise UserError(_(mensajes))
                                    else:
                                        # self.write({
                                        #     'sd_cambiar_endpoint': True
                                        # })
                                        # self.post()
                                        raise UserError(_('Hubo un error inesperado. Por favor comuniquese con su soporte \n - Fallos de internet \n -fallos de servidores siat'))
                                else:
                                    raise UserError(_('Falta alguno de estos campos: "%s"')%(res_verificacion))
        return vals

    def publicar_factura_siat(self, fact_online,codigo_control_dinamico, factura, tipo_emision_ambos_casos):
        cfg = fact_online.getConfig(fact_online.sd_codigo_modalidad, fact_online.sd_codigo_ambiente,
                                    fact_online.sd_codigo_sistema,
                                    fact_online.sd_nombre_sistema, fact_online.sd_nit_em,
                                    fact_online.sd_nombre_company, fact_online.sd_tipo_sistema, fact_online.sd_token)
        service = ServiceFacturacionElectronica() if int(fact_online.sd_codigo_modalidad) == 1 else ServiceFacturacionComputarizada()
        # service = ServiceFacturacionComputarizada()
        service.setConfig(cfg)
        service.cuis = fact_online.sd_cuis
        service.cufd = fact_online.sd_cufd
        service.codigoControl = codigo_control_dinamico
        tipo_factura = '3' if self.es_debito_credito() else fact_online.sd_tipo_factura
        if int(fact_online.sd_codigo_modalidad) == 1:
            service.validate()
        res, facturaXml = service.recepcionFactura(factura, tipo_emision_ambos_casos, tipo_factura,
                                                self.sd_es_cafc, fact_online.sd_es_test)
        if res:
            print(res)
        return res, facturaXml

    def get_documento_sector(self):
        if self.sd_codigo_documento_sector:
            if not self.type == 'out_refund':
                if self.sd_codigo_documento_sector == '1' or self.sd_codigo_documento_sector == '8' or self.sd_codigo_documento_sector == '24':
                    if self.sd_codigo_documento_sector == '1':
                        self.journal_id.sd_factura_online_id.update({
                            'sd_codigo_documento_sector': self.sd_codigo_documento_sector,
                            'sd_tipo_factura': '1'
                        })
                    elif self.sd_codigo_documento_sector == '8':
                        self.journal_id.sd_factura_online_id.update({
                            'sd_codigo_documento_sector': self.sd_codigo_documento_sector,
                            'sd_tipo_factura': '2'
                        })
                else:
                    raise UserError(_('El sistema no emite factura con este tipo de documento sector.'))

            elif self.sd_is_offline:
                monto_untaxed = self.sd_factura_original.amount_untaxed + self.sd_factura_original.sd_cantidad_gift_card
                if monto_untaxed >= self.amount_untaxed:
                    raise UserError(_('El monto total de la factura Nota Credito-Debito no puede ser mayor al de la factura original.'))
        else:
            raise UserError(_('El campo documento sector es necesario para continuar.'))
    def calcular_totales_factura(self, factura):
        self.write({
            'amount_residual': factura.cabecera.montoTotalSujetoIva if not self.es_debito_credito() else factura.cabecera.montoTotalDevuelto,
            'amount_untaxed': factura.cabecera.montoTotalSujetoIva if not self.es_debito_credito() else factura.cabecera.montoTotalDevuelto
        })
    def verificar_doc_sector(self):
        doc_sector = self.sd_codigo_documento_sector
        sin_verificacion = False
        if doc_sector in ('8','6','24'):
            sin_verificacion = True
        return sin_verificacion
    def create_evento_significativo(self, fecha_emision):
        ''' modificar para que funcione con los ultimos cambios . fechainicio datetime'''
        fecha_inicio = fecha_emision
        # fecha_inicio = datetime.strftime(hoy, '%Y-%m-%dT%H:%M:%S.%f') + '00000'
        name = datetime.strftime(fecha_inicio, 'Evento-%B-%a-%d')
        cufd = self.env['factura.cufd'].search([('sd_cufd','=',self.journal_id.sd_factura_online_id.sd_cufd)])
        data = {
            'name': name,
            'sd_factura_online_id': self.journal_id.sd_factura_online_id.id,
            'sd_fecha_inicio': fecha_inicio,
            'sd_evento_id': 2,
            'sd_cufd_id': cufd.id
        }
        return self.env['eventos.significativos.siat'].create(data)

    def verificar_monto_linea_adicional(self):
        es_descuento_invalido = False
        if self.amount_total<= 0:
            es_descuento_invalido = True
            if 0 in (invoice.price_subtotal for invoice in self.invoice_line_ids):
                monto = 'descuento de linea'
            else:
                monto = 'descuento adicional'
            self.sd_descuento_adicional = 0
        else:
            if 0 in (invoice.price_subtotal for invoice in self.invoice_line_ids):
                es_descuento_invalido = True
                monto = 'descuento de linea'
        if es_descuento_invalido:
            raise UserError(_('No se permite un descuesto del cien porciento, modifique su %s y vuelva a intentar')%(monto))

    def verificar_monto_giftcard(self):
        if self.sd_cantidad_gift_card > self.amount_total:
            self.sd_cantidad_gift_card = 0
            raise UserError(_('El monto gift-card no puede ser mayor al monto total'))
    def crear_cuf_cuis_inexistentes(self, factura):
        if not factura.existe_cuis():
            factura.solicitudCuis()
        if not factura.existe_cufd():
            factura.solicitudCufd()

    def verificar_repetidos(self, elemento, elementos):
        sw = False
        for comparar in elementos:
            if comparar.sd_codigo_clasificador == elemento:
                sw = True
        return sw

    def clean_cliente(self):

        if self.partner_id.name in ('cliente generico', 'CLIENTE GENERICO', 'Cliente Desconocido', 'Cliente Generico', 'cliente desconocido', 'CLIENTE DESCONOCIDO'):
            self.partner_id.update({
                'st_nombre_compania_facturar': '',
                'vat': '',
            })
    def obtenerListadoEventos(self, buscarId=None):
        all_eventos = self.env['mensaje.eventos.siat'].search([])
        diario = self.journal_id
        fact_online = diario.sd_factura_online_id
        # self.crear_cuf_cuis_inexistentes(fact_online)
        cfg = fact_online.getConfig(fact_online.sd_codigo_modalidad, fact_online.sd_codigo_ambiente, fact_online.sd_codigo_sistema,
                                        fact_online.sd_nombre_sistema, fact_online.sd_nit_em,
                                        fact_online.sd_nombre_company, fact_online.sd_tipo_sistema, fact_online.sd_token)

        service = ServiceSincronizacion()
        service.setConfig(cfg)
        service.cuis = fact_online.sd_cuis
        punto_venta = fact_online.sd_codigo_punto_venta if fact_online.sd_es_punto_venta else str(0)
        resEvents = service.sincronizarParametricaEventosSignificativos(fact_online.sd_codigo_sucursal, punto_venta)

        if resEvents:
            for event in resEvents['listaCodigos']:
                if not self.verificar_repetidos(event, all_eventos):
                    self.env['mensaje.eventos.siat'].create({
                        'sd_codigo_clasificador': event['codigoClasificador'],
                        'sd_descripcion': event['descripcion']
                    })
        # if buscarId is None:
        #     return resEvents
        #
        # event = None
        # for parametrica in resEvents['listaCodigos']:
        #     if parametrica['codigoClasificador'] == buscarId:
        #         event = parametrica
        #         break

        # return event



    def verificar_campos(self, pv):
        fact = self.journal_id.sd_factura_online_id
        if not self.sd_cuf:
            raise UserError(_('Debe tener un cuf para continuar'))
        if not fact.sd_cuis:
            raise UserError(_('Debe tener un cuis para continuar'))
        if not fact.sd_cufd:
            raise UserError(_('Debe tener un cufd para continuar'))
        if not self.sd_motivo_id.sd_codigo_clasificador:
            raise UserError(_('Debe tener un codigo de motivo para continuar'))
        if not fact.sd_codigo_sucursal:
            raise UserError(_('Debe tener codigo sucursal para continuar'))
        if not self.sd_codigo_documento_sector:
            raise UserError(_('Debe tener codigo de documento sector para continuar'))
        if fact.sd_es_punto_venta:
            if not pv:
                raise UserError(_('Debe tener codigo punto venta para continuar'))
        if not fact.sd_tipo_sistema:
            raise UserError(_('Debe tener tipo de sistema para continuar'))
        if not fact.sd_tipo_emision:
            raise UserError(_('Debe tener tipo de emisión para continuar'))



    def anular_factura(self, es_masiva=None):
        if self.journal_id.sd_factura_online_id.verificar_grupo_anular():
            if self.state != 'draft' and self.sd_cuf:
                diario = self.journal_id
                fact_online = diario.sd_factura_online_id
                punto_venta = fact_online.sd_codigo_punto_venta.sd_codigo_punto_venta if fact_online.sd_es_punto_venta else 0

                if not fact_online.existe_cufd():
                    fact_online.solicitudCufd()

                self.verificar_campos(punto_venta)
                documeto_sector = self.sd_codigo_documento_sector if not self.es_debito_credito() else 24
                tipo_factura = fact_online.sd_tipo_factura if not self.es_debito_credito() else 3
                cfg = fact_online.getConfig(fact_online.sd_codigo_modalidad, fact_online.sd_codigo_ambiente,
                                            fact_online.sd_codigo_sistema,
                                            fact_online.sd_nombre_sistema, fact_online.sd_nit_em,
                                            fact_online.sd_nombre_company, fact_online.sd_tipo_sistema, fact_online.sd_token)
                service = ServiceFacturacion()
                service.setConfig(cfg)
                service.cuis = fact_online.sd_cuis
                service.cufd = fact_online.sd_cufd
                res_anulacion = service.anulacionFactura(self.sd_motivo_id.sd_codigo_clasificador,self.sd_cuf,fact_online.sd_codigo_sucursal,
                                         punto_venta,tipo_factura,fact_online.sd_tipo_emision,
                                         documeto_sector)
                if res_anulacion:
                    print('Anulacion factura: ', res_anulacion)
                    if res_anulacion['transaccion'] == True:
                        self.write({
                            'sd_codigo_descripcion': res_anulacion['codigoDescripcion']
                        })
                        if not es_masiva:
                            mjs = fact_online.mensaje_personalizador('Se anulo correctamente la factura.')
                            return mjs
                    else:
                        mensaje = res_anulacion['codigoDescripcion'] + '\n'
                        for mensaje_anulacion in res_anulacion['mensajesList']:
                            mensaje = mensaje + mensaje_anulacion['descripcion'] + '\n'
                        if res_anulacion['mensajesList'][0]['descripcion'] != 'LA FACTURA O NOTA DE CREDITO-DEBITO ' \
                                                'YA SE ENCUENTRA ANULADA' and not fact_online.sd_es_test:
                            raise UserError(_(mensaje))

                        # mensaje = res_anulacion['codigoDescripcion'] + '\n'
                        # for mensaje_anulacion in res_anulacion['mensajesList']:
                        #     mensaje = mensaje + mensaje_anulacion['descripcion'] + '\n'
                        # if not fact_online.sd_es_test:
                        #     raise UserError(_(mensaje))
                else:
                    raise UserError(_('No es posible continuar \n comuniquese con su soporte.'))

    def button_cancel(self, es_masiva=None):
        if self.journal_id.fcb_es_electronico and self.type in ("out_invoice", "out_refund"):
            if self.env.user.has_group('sd_facturacion_en_linea_v13.sd_anulacion_factura_group'):
                res = self.verificar_estado_factura_siat()
                if res:
                    if self.verificar_estado_factura_siat()['codigoDescripcion'] != 'ANULADA':
                        self.anular_factura(es_masiva=es_masiva)
                else:
                    self.anular_factura(es_masiva=es_masiva)
            else:
                raise UserError(_('No pertenece a un grupo con permisos para realizar la acción'))
        vals = super(FacturaAccountMove, self).button_cancel()
        return vals

    def button_draft(self):
        vals = super(FacturaAccountMove, self).button_draft()
        print(self.env['res.users'].has_group('sd_facturacion_en_linea_v13.sd_facturacion_electronica_en_linea_group'))
        if self.journal_id.fcb_es_electronico:
            if not self.env['res.users'].has_group('sd_facturacion_en_linea_v13.sd_anulacion_factura_group'):
                raise UserError(_('No pertenece a un grupo con permisos para realizar la acción'))
        return vals

#     modificar endpoint
    def cambiar_endpoint(self):
        print('cambio a fuera de linea')
        fact_online = self.journal_id.sd_factura_online_id
        nuevo_end_point = not fact_online.sd_cambiar_endpoint
        if nuevo_end_point:
            # cudf_evento = self.env['factura.cufd'].search([('sd_cufd', '=', fact_online.sd_cufd)])
            self.crear_evento_significativo()
            fact_online.write({
                'sd_cambiar_endpoint': nuevo_end_point,
                'sd_tipo_emision': '2',
            })
        else:
            fact_online.write({
                'sd_cambiar_endpoint': nuevo_end_point,
                'sd_tipo_emision': '1',
            })

    def crear_evento_significativo(self):
        fact_online = self.journal_id.sd_factura_online_id
        cudf_evento = self.env['factura.cufd'].search([('sd_cufd', '=', fact_online.sd_cufd)])
        vals = {
                'sd_cufd_id': cudf_evento.id,
                'sd_fecha_inicio': datetime.now()
                }
        sd_evento_significativo = self.env['eventos.significativos.siat'].create(vals)
        fact_online.write({
            'sd_evento_significativo_id': sd_evento_significativo.id
        })

    # verificar estado de factura
    def action_verificar_factura_siat(self, es_masiva=None):
        fact_online = self.journal_id.sd_factura_online_id
        if not fact_online.existe_cufd():
            fact_online.solicitudCufd()

        res = self.verificar_estado_factura_siat()
        # print('verificar factura', res)
        if res['codigoDescripcion']!='RECHAZADA':
            if res['codigoDescripcion'] == 'VALIDA':
                estado_siat = 'valida'
            if res['codigoDescripcion'] == 'ANULADA':
                estado_siat = 'anulada'
            self.write({
                'sd_estado_siat': estado_siat
            })
            if not es_masiva:
                mjs = fact_online.mensaje_personalizador('Se actualizo correctamente el estado de la factura desde impuestos nacionales')
                return mjs
    def verificar_estado_factura_siat(self):
        fact_online = self.journal_id.sd_factura_online_id
        punto_venta = fact_online.sd_codigo_punto_venta.sd_codigo_punto_venta if fact_online.sd_es_punto_venta else 0
        cfg = fact_online.getConfig(fact_online.sd_codigo_modalidad, fact_online.sd_codigo_ambiente,
                                    fact_online.sd_codigo_sistema,
                                    fact_online.sd_nombre_sistema, fact_online.sd_nit_em,
                                    fact_online.sd_nombre_company, fact_online.sd_tipo_sistema, fact_online.sd_token)
        service = ServiceFacturacion()
        service.setConfig(cfg)
        service.cuis = fact_online.sd_cuis
        service.cufd = fact_online.sd_cufd
        res_verificar = service.verificarEstadoFactura(punto_venta,fact_online.sd_codigo_sucursal,self.sd_codigo_documento_sector,
                                                       fact_online.sd_tipo_emision,fact_online.sd_tipo_factura,self.sd_cuf)
        if res_verificar:
            print('verificacion de factura',res_verificar)
        return res_verificar


    # def action_verificar_facturas_multiples(self):
    #     for move in self:
    #         move.action_verificar_factura_siat()
    #     return True
    def verificar_nit_valido(self, not_return=None):
        if int(self.sd_codigo_tipo_documento) == 5:
            emision = self.journal_id.sd_factura_online_id.sd_tipo_emision
            if not int(emision) == 2 and not self.sd_es_cafc:
                res_nit = self.journal_id.sd_factura_online_id.verificar_nit_valido(self.sd_nro_documento_facturado)
                if res_nit:
                    if res_nit['transaccion'] == False:
                        msg = res_nit['mensajesList'][0]['descripcion']
                        self.sd_codigo_excepcion = 1
                        self.write({
                            'sd_codigo_excepcion': 1
                        })
                    else:
                        msg = res_nit['mensajesList'][0]['descripcion']
                        self.sd_codigo_excepcion = 0
                        self.write({
                            'sd_codigo_excepcion': 0
                        })
                    if not not_return:
                        return self.journal_id.sd_factura_online_id.mensaje_personalizador(msg)
        else:
            self.sd_codigo_excepcion = 0
            self.write({
                'sd_codigo_excepcion': 0
            })

    def get_cufd_evento(self):
        '''
            funcion auxiliar para obtener el cufd del evento con cafc
        :return: no retorna
        '''
        if self.sd_es_cafc:
            fecha_factura = self.sd_fecha_emision
            fecha_limite_pasada = fecha_factura - timedelta(days=30)
            cufd_en_rango_id = self.env['factura.cufd'].search([('sd_facturacion_online_id','=',self.journal_id.sd_factura_online_id.id),('sd_fecha_vigencia','>=',fecha_factura)], order="sd_fecha_vigencia")
            if cufd_en_rango_id:
                cufd_interno_ids = []
                for cufd_in in cufd_en_rango_id:
                    if cufd_in.sd_fecha_vigencia - timedelta(hours=24) <= fecha_factura:
                        cufd_interno_ids.append(cufd_in.id)

                cufd_res_id = self.env['factura.cufd'].search([('sd_facturacion_online_id','=',self.journal_id.sd_factura_online_id.id), ('id', 'in', cufd_interno_ids)],
                                                              order="sd_fecha_vigencia desc", limit=1)
                if cufd_res_id:
                    cufd_evento_id = cufd_res_id
                else:
                    cufd_pasado_id = self.env['factura.cufd'].search([('sd_facturacion_online_id','=',self.journal_id.sd_factura_online_id.id),('sd_fecha_vigencia','<=',fecha_factura),('sd_fecha_vigencia','>=',fecha_limite_pasada)], order="sd_fecha_vigencia desc", limit=1)
                    cufd_evento_id = cufd_pasado_id
            print('Cufd evento obtenido',cufd_evento_id.sd_fecha_string)
            return cufd_evento_id

    def open_wizard_anular_factura(self):
        self.ensure_one()
        # self.validaciones_para_crear_account_payment()
        action = self.env.ref('sd_facturacion_en_linea_v13.sd_action_create_wizard_anular_factura').read()[0]
        return action
    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'sd_descuento_adicional'
    )
    def _compute_amount(self):
        vals = super(FacturaAccountMove, self)._compute_amount()

        for move in self:
            if move.sd_is_facturacion_linea and move.type =='out_invoice':
                move.amount_total = move.amount_total - move.sd_descuento_adicional
                move.amount_residual = move.amount_residual -move.sd_descuento_adicional
        return vals

