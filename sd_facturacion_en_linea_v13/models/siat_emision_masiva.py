from odoo import api, fields, models, _
from pysiat.services.service_operaciones import ServiceOperaciones
import pysiat.functions as functions
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from datetime import timedelta
from pysiat.invoices.CompraVenta import CompraVenta
from pysiat.services.service_facturacion_computarizada import ServiceFacturacionComputarizada
from pysiat.services.service_facturacion_electronica import ServiceFacturacionElectronica
import pysiat.constants as constants

FacturasCuf = ''
class SdSiatEmisionMasiva(models.Model):
    _name = 'siat.emision.masiva'
# cafc= 101474BF9939D
    name = fields.Char(string='Nombre')
    sd_factura_online_id = fields.Many2one('online.billing.siat', string='Factura en Linea', required=True)
    sd_cuis = fields.Char(related='sd_factura_online_id.sd_cuis', string='Cuis',)
    sd_journal_id = fields.Many2one('account.journal', related='sd_factura_online_id.sd_journal_id')
    sd_cufd_id = fields.Many2one('factura.cufd', string='Cufd')
    sd_evento_id = fields.Many2one('eventos.significativos.siat', string='Evento Significativo')
    sd_codigo_sucursal = fields.Selection([('0', 'Casa Matriz'),
                                           ('1', 'Sucursal 1'), ],related='sd_factura_online_id.sd_codigo_sucursal', string='Codigo Sucursal')
    sd_es_punto_venta = fields.Boolean(string='es punto de venta',related='sd_factura_online_id.sd_es_punto_venta')
    sd_codigo_punto_venta = fields.Many2one('punto.venta.factura', string='Código punto Venta',related='sd_factura_online_id.sd_codigo_punto_venta')
    sd_cafc = fields.Char(string='CAFC',help='Se coloca el CAFC de la factura manual en caso de Existir')
    sd_tipo_factura = fields.Selection([('1', 'Tipo factura credito fiscal'),
                                        ('2', 'Tipo factura sin credito fiscal'),
                                        ('3', 'Tipo factura ajuste')],
                                       string='Tipo factura',
                                       default='1', related='sd_factura_online_id.sd_tipo_factura')
    sd_fecha_facturas = fields.Date(string='Fecha de facturas')
    sd_codigo_documento_sector = fields.Selection([('1', 'FACTURA COMPRA-VENTA'),
                                                   ('2', 'FACTURA DE ALQUILER DE BIENES INMUEBLES'),
                                                   ('3', 'FACTURA COMERCIAL DE EXPORTACIÓN'),
                                                   ('4', 'FACTURA COMERCIAL DE EXPORTACIÓN EN LIBRE CONSIGNACIÓN'),
                                                   ('5', 'FACTURA DE ZONA FRANCA'),
                                                   ('6', 'FACTURA DE SERVICIO TURÍSTICO Y HOSPEDAJE'),
                                                   ('7', 'FACTURA DE COMERCIALIZACIÓN DE ALIMENTOS – SEGURIDAD'),
                                                   ('8', 'FACTURA DE TASA CERO POR VENTA DE LIBROS Y TRANSPORTE INTERNACIONAL DE CARGA'),
                                                   ('9', 'FACTURA DE COMPRA Y VENTA DE MONEDA EXTRANJERA'),
                                                   ('10', 'FACTURA DUTTY FREE'),
                                                   ('11', 'FACTURA SECTORES EDUCATIVOS'),
                                                   ('12', 'FACTURA DE COMERCIALIZACIÓN DE HIDROCARBUROS'),
                                                   ('13', 'FACTURA DE SERVICIOS BÁSICOS'),
                                                   ('14', 'FACTURA PRODUCTOS ALCANZADOS POR EL ICE'),
                                                   ('15', 'FACTURA DE ENTIDADES FINANCIERAS'),
                                                   ('16', 'FACTURA DE HOTELES'),
                                                   ('17', 'FACTURA DE HOSPITALES/CLÍNICAS'),
                                                   ('18', 'FACTURA DE JUEGOS DE AZAR'),
                                                   ('19', 'FACTURA HIDROCARBUROS ALCANZADA IEHD'),
                                                   ('20', 'FACTURA COMERCIAL DE EXPORTACIÓN DE MINERALES'),
                                                   ('21', 'FACTURA VENTA INTERNA MINERALES'),
                                                   ('22', 'FACTURA TELECOMUNICACIONES'),
                                                   ('23', 'FACTURA PREVALORADA'),
                                                   ('24', 'NOTA DE CRÉDITO-DÉBITO'),
                                                   ('28', 'FACTURA COMERCIAL DE EXPORTACIÓN DE SERVICIOS'),
                                                   ('29', 'NOTA DE CONCILIACION'),
                                                   ('30', 'BOLETO AEREO'),
                                                   ('31', 'FACTURA DE SUMINISTRO'),
                                                   ('32', 'FACTURA ICE ZONA FRANCA'),
                                                   ('33', 'FACTURA TASA CERO BIENES CAPITAL'),
                                                   ('34', 'FACTURA DE SEGUROS'),
                                                   ('35', 'FACTURA COMPRA VENTA BONIFICACIONES'),
                                                   ('36', 'FACTURA PREVALORADA SDCF'),
                                                   ('37', 'FACTURA DE COMERCIALIZACIÓN DE GNV'),
                                                   ('38', 'FACTURA HIDROCARBUROS NO ALCANZADA IEHD'),
                                                   ('39', 'FACTURA COMERCIALIZACION GN y GLP'),
                                                   ('40', 'FACTURA DE SERVICIOS BÁSICOS ZF'),
                                                   ('41', 'FACTURA COMPRA VENTA TASAS'),
                                                   ('42', 'FACTURA ALQUILER ZF'),
                                                   ('43', 'FACTURA COMERCIAL DE EXPORTACIÓN HIDROCARBUROS'),
                                                   ('44', 'FACTURA IMPORTACION COMERCIALIZACION LUBRICANTES')],
                                                  string='Tipo Documento sector', related='sd_factura_online_id.sd_codigo_documento_sector')
    sd_invoice_ids = fields.One2many('account.move','sd_siat_emision_masiva_id',string='Facturas',
                                     domain="[('journal_id.fcb_es_electronico','=',True),('type','=','out_invoice'),('state','=','draft'),('journal_id','=',sd_journal_id)]")

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('recepcion', 'Recepcion Masiva'),
        ('validate', 'Validacion Masiva'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='draft')
    # status_name = fields.Char(related='state', store=True, copy=False)
    sd_codigo_recepcion_masiva = fields.Char('Código Recepcion Paquetes')
    sd_motivo_online = fields.Many2one('motivo.anulacion.siat', string='Motivo de Anulación')
    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)


    def construirFacturas(self, cfg, fact_online, esBot=None, esPaquete=None, test=None):

        facturas = []
        # fecha_emision = self.sd_fecha_inicio + timedelta(minutes=1)
        # print('fecha emision antes de factura', fecha_emision)
        for invoice in self.sd_invoice_ids:
            # print('contruir facturas paquete', invoice.name)
            factura = invoice.construir_factura(
                cfg['modalidad'],
                esBot=esBot,
                esPaquete=esPaquete,
                test=test
            )

            factura.cabecera.nitEmisor = cfg['nit']
            factura.cabecera.razonSocialEmisor = cfg['razonSocial']
            invoice.write({
                'sd_nro_factura_siat': factura.cabecera.numeroFactura
            })

            factura.cabecera.cufd = self.sd_factura_online_id.sd_cufd
            # factura.cabecera.cafc = self.get_cafc()
            facturas.append(factura)
            # fechaEmision = self.sd_fecha_inicio + timedelta(0, 10)
        return facturas

    def cargar_facturas_paquetes(self):
        if self.sd_fecha_facturas:
            fecha = self.sd_fecha_facturas
            facturas = self.env['account.move'].search([('sd_es_cafc', '=', True)]).filtered(
                lambda s: s.date == fecha)
            self.update({
                'sd_invoice_ids': [factura.id for factura in facturas]
            })
        else:
            raise UserError(
                _('Por favor ingrese las fechas de inicio y fin para obtener las facturas correspondientes'))

    def registroEmisionMasiva(self, test=None, esBot=None):
        if self.state == 'draft':
            self.update({
                'state': 'recepcion'
            })
            fact_online = self.sd_factura_online_id
            if fact_online.verificar_grupo_admin() or fact_online.verificar_grupo_user():
                self.validar_campos_necesarios()

                cfg = fact_online.getConfig(fact_online.sd_codigo_modalidad, fact_online.sd_codigo_ambiente,
                                            fact_online.sd_codigo_sistema,
                                            fact_online.sd_nombre_sistema, fact_online.sd_nit_em,
                                            fact_online.sd_nombre_company, fact_online.sd_tipo_sistema, fact_online.sd_token)

                if not fact_online.existe_cufd():
                    fact_online.solicitudCufd()

                facturas = self.construirFacturas(cfg, fact_online, esBot=esBot, esPaquete=False, test=test)

                res_paquete_facturas = self.recepcionMasivaFactura(cfg, facturas,  self.sd_tipo_factura, cafc=self.get_cafc())


                # print('recepcion Masiva', res_paquete_facturas)

                if res_paquete_facturas:
                    if res_paquete_facturas['codigoDescripcion'] == 'PENDIENTE':
                        self.update({
                            'sd_codigo_recepcion_masiva': res_paquete_facturas['codigoRecepcion'],
                            'state': 'recepcion'
                        })
                        # print('publicar facturas-------------------')
                        for factura in self.sd_invoice_ids:
                            factura.update({
                                'sd_codigo_recepcion': res_paquete_facturas['codigoRecepcion']
                            })
                            factura.post(esMasiva=True)
                        # print('cuf y url-------------------')
                        for factura in facturas:
                            dominio = 'siat.impuestos.gob.bo' if fact_online.sd_codigo_ambiente == '1' else 'pilotosiat.impuestos.gob.bo'
                            url = 'https://' + dominio + '/consulta/QR?nit={0}&cuf={1}&numero={2}&t=2'.format(
                                fact_online.sd_nit_em,
                                factura.cabecera.cuf,
                                factura.cabecera.numeroFactura
                            )
                            fact_posted = self.env['account.move'].search([('sd_nro_factura_siat','=',factura.cabecera.numeroFactura),
                                                                           ('journal_id', '=', self.sd_factura_online_id.sd_journal_id.id)])
                            fact_posted.write({
                                'sd_cuf': factura.cabecera.cuf,
                                'sd_url_factura': url,
                                'sd_leyenda_id': self.get_leyenda(factura.cabecera.leyenda),
                                'sd_monto_total_sujeto_iva': factura.cabecera.montoTotalSujetoIva,
                                'sd_monto_total_moneda': factura.cabecera.montoTotalMoneda,
                                'sd_nombre_facturado': factura.cabecera.nombreRazonSocial,
                                'sd_tipo_documento_facturado': str(factura.cabecera.codigoTipoDocumentoIdentidad),
                                'sd_nro_documento_facturado': factura.cabecera.numeroDocumento,
                                'sd_extension': factura.cabecera.complemento if factura.cabecera.complemento else ''
                            })
                        # print('fin de la publicacion-------------------')
                        if not test and not esBot:
                            mjs = fact_online.mensaje_personalizador('Recepción de Masiva éxitosa.')
                            return mjs
                    else:
                        if not test and not esBot:
                            mensaje = ''
                            for mensaje_diccionario in res_paquete_facturas['mensajesList']:
                                mensaje = mensaje + mensaje_diccionario['descripcion'] + '\n'
                            raise UserError(_('La operación no se pudo completar por: \n "%s"') % (mensaje))
                else:
                    raise UserError(_('No es posible continuar. \n Comuníquese con su soporte.'))

    def recepcionMasivaFactura(self, cfg, facturas: list, tipoFactura, cafc=None):
        if self.sd_factura_online_id.verificar_grupo_admin() or self.sd_factura_online_id.verificar_grupo_user():
            service = ServiceFacturacionElectronica() if int(self.sd_factura_online_id.sd_codigo_modalidad) == 1 else ServiceFacturacionComputarizada()
            service.setConfig(cfg)
            service.cuis = self.sd_factura_online_id.sd_cuis
            service.cufd = self.sd_factura_online_id.sd_cufd
            service.codigoControl = self.sd_factura_online_id.sd_codigo_control  # resCufd['codigoControl']

            res = service.recepcionMasivaFactura(
                facturas,
                constants.TIPO_EMISION_MASIVA,
                int(tipoFactura),
                cafc=cafc
            )
            return res

    def get_leyenda(self, descripcion):
        leyenda_id = self.env['leyenda.factura.siat'].search([('sd_descripcion_leyenda','=',descripcion)], limit=1)
        return leyenda_id.id if leyenda_id.id else None

    def validacionRecepcionMasiva(self, sucursal: int=None, puntoventa: int=None, documentoSector: int=None, tipoFactura: int=None,
                                   codigoRecepcion=None, test=None, esBot=None):
        if self.sd_factura_online_id.verificar_grupo_admin() or self.sd_factura_online_id.verificar_grupo_user():
            fact_online = self.sd_factura_online_id
            cfg = fact_online.getConfig(fact_online.sd_codigo_modalidad, fact_online.sd_codigo_ambiente,
                                        fact_online.sd_codigo_sistema,
                                        fact_online.sd_nombre_sistema, fact_online.sd_nit_em,
                                        fact_online.sd_nombre_company, fact_online.sd_tipo_sistema, fact_online.sd_token)
            sucursal = sucursal or fact_online.sd_codigo_sucursal
            puntoventa = puntoventa or self.sd_factura_online_id.sd_codigo_punto_venta.sd_codigo_punto_venta if self.sd_factura_online_id.sd_es_punto_venta else 0
            codigoRecepcion = codigoRecepcion or self.sd_codigo_recepcion_masiva
            tipoFactura = tipoFactura or self.sd_tipo_factura
            documentoSector = documentoSector or int(self.sd_codigo_documento_sector)
            service = ServiceFacturacionElectronica() if int(self.sd_factura_online_id.sd_codigo_modalidad) == 1 else ServiceFacturacionComputarizada()
            service.setConfig(cfg)
            service.cuis = self.sd_factura_online_id.sd_cuis
            service.cufd = self.sd_factura_online_id.sd_cufd
            res = service.validacionRecepcionMasivaFactura(sucursal, puntoventa, codigoRecepcion, tipoFactura,
                                                            documentoSector)
            # print('validacion masiva', res)

            if res:
                if res['codigoDescripcion'] == 'VALIDADA':
                    self.write({
                        'state': 'validate'
                    })
                    # if not esBot:
                    #     i = 0
                    #     for invoice in self.sd_invoice_ids:
                    #         fact_cuf = FacturasCuf[i]
                    #         invoice.write({
                    #             'sd_nro_factura_siat': fact_cuf.cabecera.numeroFactura
                    #         })
                    #         invoice.action_post()

                        # for factura in FacturasCuf:
                        #     print(factura.cabecera.cuf)
                        # url = 'https://pilotosiat.impuestos.gob.bo/consulta/QR?nit={0}&cuf={1}&numero={2}&t=1'.format(
                        #         cfg['nit'],
                        #         factura.cabecera.cuf,
                        #         factura.cabecera.numeroFactura
                        #     )
                        #     fact_unposted = self.env['account.move'].search([('sd_nro_factura_siat','=',factura.cabecera.numeroFactura)])
                        #     fact_unposted.write({
                        #         'sd_cuf': factura.cabecera.cuf,
                        #         'sd_url_factura': url
                        #     })

                    if not test and not esBot:
                        mjs = fact_online.mensaje_personalizador('Validación Masiva de Facturas éxitosa.')
                        return mjs
                else:
                    if not test and not esBot:
                        mensaje = ''
                        for mensaje_diccionario in res['mensajesList']:
                            mensaje = mensaje + mensaje_diccionario['descripcion'] + '\n'
                        raise UserError(_('Observada: \n "%s"')%(mensaje))
            else:
                raise UserError(_('Hubo un error inesperado, por favor verifique su conexión a internet y vuelva a intentar.\nConsulte a su soporte si intento lo anterior'))
            return res

    def get_cafc(self):
        if self.sd_cafc:
            return str(self.sd_cafc)
        else:
            return None

    def action_enviar_correo_masivo(self):
        fact_online = self.sd_factura_online_id
        for factura in self.sd_invoice_ids:
            factura.action_imprimir_factura_enviar_correo_siat()
        mjs = fact_online.mensaje_personalizador('Se ha enviado correctamente las facturas a los correos')
        return mjs

    def wizard_pagos_masivo_factura(self):
        self.ensure_one()
        # self.validaciones_para_crear_account_payment()
        action = self.env.ref('sd_facturacion_en_linea_v13.sd_action_create_wizard_pagos_factura_masiva').read()[0]
        return action

    def action_verificar_estado_facturas_siat(self):
        ''' verificar si una factura ya esta publicada y se vuelve a borrador,
        posiblemente se deba verificar todas las facturas hasta las de borrador'''
        fact_online = self.sd_factura_online_id
        for invoice_id in self.sd_invoice_ids:
            if invoice_id.state != 'draft':
                invoice_id.action_verificar_factura_siat(es_masiva=True)
        mjs = fact_online.mensaje_personalizador('Se ha actualizado el estado de siat en las facturas')
        return mjs
    def action_anular_factura_masiva(self):
        grupo_anular = self.sd_factura_online_id.verificar_grupo_anular()
        fact_online = self.sd_factura_online_id
        if grupo_anular:
            for invoice_id in self.sd_invoice_ids:
                if invoice_id.state == 'posted':
                    invoice_id.write({
                        'sd_motivo_id': self.sd_motivo_online.id
                    })
                    invoice_id.button_cancel(es_masiva=True)
            self.write({'state': 'cancel'})
            mjs = fact_online.mensaje_personalizador('Se han anulado las facturas correctamente')
        return mjs

    def validar_campos_necesarios(self):

        if not self.name:
            raise UserError(_('Es necesario el campo Nombre para continuar'))
        if not self.sd_factura_online_id:
            raise UserError(_('Es necesario el campo Factura en Linea para continuar'))
        if not self.sd_cuis:
            raise UserError(_('Es necesario el campo Cuis para continuar'))
        # if not self.sd_cufd_id:
        #     raise UserError(_('Es necesario el campo Cufd para continuar'))
        # if not self.sd_fecha_inicio:
        #     raise UserError(_('Es necesario el campo Fecha de Inicio para continuar'))
        # if not self.sd_fecha_fin:
        #     raise UserError(_('Es necesario el campo Fecha Fin para continuar'))
        # if not self.sd_evento_id:
        #     raise UserError(_('Es necesario el campo Contigencia para continuar'))
        if not self.sd_codigo_sucursal:
            raise UserError(_('Es necesario el campo Código sucursal para continuar'))
        if not self.sd_codigo_punto_venta:
            if self.sd_es_punto_venta:
                raise UserError(_('Es necesario el campo Código punto de venta para continuar'))
        if not self.sd_tipo_factura:
            raise UserError(_('Es necesario el campo Tipo de factura para continuar'))
        if not self.sd_codigo_documento_sector:
            raise UserError(_('Es necesario el campo Código documento de sector para continuar'))
        if not self.sd_invoice_ids:
            raise UserError(_('Seleccione al menos una factura para continuar'))


    # def cargar_facturas_paquetes(self):
    #     if self.sd_fecha_inicio and self.sd_fecha_fin:
    #         fecha_inicio = self.sd_fecha_inicio
    #         fecha_fin = self.sd_fecha_fin
    #         facturas = self.env['account.move'].search([('sd_es_cafc','=',True)]).filtered(lambda s: s.sd_fecha_emision > fecha_inicio and s.sd_fecha_emision < fecha_fin or
    #                       s.sd_fecha_emision == fecha_inicio or s.sd_fecha_emision == fecha_fin)
    #         self.update({
    #             'sd_invoice_ids': [factura.id for factura in facturas]
    #         })
    #     else:
    #         raise UserError(_('Por favor ingrese las fechas de inicio y fin para obtener las facturas correspondientes'))
