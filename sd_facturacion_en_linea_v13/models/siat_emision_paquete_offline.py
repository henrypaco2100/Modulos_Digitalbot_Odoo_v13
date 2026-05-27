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
class SdSiatEmisionPaqueteOffline(models.Model):
    _name = 'siat.emision.paquete.offline'
# cafc= 101474BF9939D
    name = fields.Char(string='Nombre')
    sd_factura_online_id = fields.Many2one('online.billing.siat', string='Factura en Linea', required=True)
    sd_cuis = fields.Char(related='sd_evento_id.sd_cuis', string='Cuis',)
    sd_journal_id = fields.Many2one('account.journal', related='sd_factura_online_id.sd_journal_id')
    sd_cufd_id = fields.Many2one('factura.cufd', string='Cufd', related='sd_evento_id.sd_cufd_id')
    sd_fecha_inicio = fields.Datetime(string='Fecha de Inicio',related='sd_evento_id.sd_fecha_inicio')
    sd_fecha_fin = fields.Datetime(string='Fecha Fin', related='sd_evento_id.sd_fecha_fin')
    sd_evento_id = fields.Many2one('eventos.significativos.siat', string='Evento Significativo')
    sd_codigoControlAntiguo = fields.Char(string='Codigo de Control', related='sd_evento_id.sd_cufd_id.sd_codigo_control')
    sd_codigo_sucursal = fields.Selection([('0', 'Casa Matriz'),
                                           ('1', 'Sucursal 1'), ],related='sd_factura_online_id.sd_codigo_sucursal', string='Codigo Sucursal')
    sd_es_punto_venta = fields.Boolean(string='es punto de venta',related='sd_factura_online_id.sd_es_punto_venta')
    sd_codigo_punto_venta = fields.Many2one('punto.venta.factura', string='Código punto Venta',related='sd_factura_online_id.sd_codigo_punto_venta')
    sd_cafc = fields.Char(string='CAFC',help='Se coloca el CAFC de la factura manual en caso de Existir')
    sd_tipo_factura = fields.Selection([('1', 'Tipo factura credito fiscal'),
                                        ('2', 'Tipo factura sin credito fiscal'),
                                        ('3', 'Tipo factura ajuste')],
                                       string='Tipo factura',
                                       default='1')
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
                                                  string='Tipo Documento sector', default='1')
    sd_invoice_ids = fields.One2many('account.move','sd_sia_emision_paquete_id',string='Facturas',
                                     domain="[('journal_id.fcb_es_electronico','=',True),('type','=','out_invoice'),('journal_id','=',sd_journal_id)]")

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('recepcion', 'Recepcion de Paquetes'),
        ('validate', 'Validacion de Paquetes')
    ], string='Estado', default='draft')
    sd_codigo_recepcion_paquetes = fields.Char('Código Recepcion Paquetes')
    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)

    def construirFacturas(self, cfg,fact_online, esBot=None, esPaquete=None, test=None):

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

            factura.cabecera.cufd = self.sd_cufd_id.sd_cufd
            # factura.cabecera.cafc = self.get_cafc()
            facturas.append(factura)
            # fechaEmision = self.sd_fecha_inicio + timedelta(0, 10)
        return facturas
    
    def cargar_facturas_paquetes(self):
        if self.sd_fecha_inicio and self.sd_fecha_fin:
            fecha_inicio = self.sd_fecha_inicio
            fecha_fin = self.sd_fecha_fin
            facturas = self.env['account.move'].search([('sd_es_cafc','=',True)]).filtered(lambda s: s.sd_fecha_emision > fecha_inicio and s.sd_fecha_emision < fecha_fin or
                          s.sd_fecha_emision == fecha_inicio or s.sd_fecha_emision == fecha_fin)
            self.update({
                'sd_invoice_ids': [factura.id for factura in facturas]
            })
        else:
            raise UserError(_('Por favor ingrese las fechas de inicio y fin para obtener las facturas correspondientes'))
    def registroEmisionPaquetes(self, test=None, esBot=None):
        if self.sd_factura_online_id.verificar_grupo_admin():
            self.validar_campos_necesarios()
            fact_online = self.sd_factura_online_id
            cfg = fact_online.getConfig(fact_online.sd_codigo_modalidad, fact_online.sd_codigo_ambiente,
                                        fact_online.sd_codigo_sistema,
                                        fact_online.sd_nombre_sistema, fact_online.sd_nit_em,
                                        fact_online.sd_nombre_company, fact_online.sd_tipo_sistema, fact_online.sd_token)

            facturas = self.construirFacturas(cfg, fact_online, esBot=esBot, esPaquete=True, test=self.sd_fecha_inicio)
            codigo_control = self.sd_codigoControlAntiguo

            res_paquete_facturas = self.recepcionPaqueteFactura(cfg, facturas, codigo_control, self.sd_tipo_factura,
                                                                self.sd_evento_id, cafc=self.get_cafc())

            # print('recepcion paquetes', res_paquete_facturas)

            if res_paquete_facturas:
                if res_paquete_facturas['codigoDescripcion'] == 'PENDIENTE':
                    self.write({
                        'sd_codigo_recepcion_paquetes': res_paquete_facturas['codigoRecepcion'],
                        'state': 'recepcion'
                    })
                    for factura in self.sd_invoice_ids:
                        factura.write({
                            'sd_codigo_recepcion': self.sd_codigo_recepcion_paquetes
                        })
                    # if not esBot:
                    #     for factura in facturas:
                    #         print(factura.cabecera.cuf)
                    #         url = 'https://pilotosiat.impuestos.gob.bo/consulta/QR?nit={0}&cuf={1}&numero={2}&t=1'.format(
                    #             cfg['nit'],
                    #             factura.cabecera.cuf,
                    #             factura.cabecera.numeroFactura
                    #         )
                    #         fact_unposted = self.env['account.move'].search([('sd_nro_factura_siat','=',factura.cabecera.numeroFactura)])
                    #         fact_unposted.write({
                    #             'sd_cuf': factura.cabecera.cuf,
                    #             'sd_url_factura': url
                    #         })
                    if not test and not esBot:
                        mjs = fact_online.mensaje_personalizador('Recepción de paquetes éxitosa.')
                        return mjs
                else:
                    if not test and not esBot:
                        mensaje = ''
                        for mensaje_diccionario in res_paquete_facturas['mensajesList']:
                            mensaje = mensaje + mensaje_diccionario['descripcion'] + '\n'
                        raise UserError(_('La operación no se pudo completar por: \n "%s"') % (mensaje))
            else:
                raise UserError(_('No es posible continuar. \n Comuníquese con su soporte.'))

    # def get_codigo_control(self):
    #     '''
    #         obtiene el codigo de control segun sea el caso de los evento
    #         tipo 1: (1,2,3,4)
    #         tipo 2: (5,6,7)
    #     '''
    #     evento = self.sd_evento_id.sd_evento_id.sd_codigo_clasificador
    #     if evento in (1,2,3,4):
    #         codigo_control = self.sd_codigoControlAntiguo
    #     else:
    #         codigo_control = self.sd_factura_online_id.sd_codigo_control
    #     return codigo_control
        

    def validacionRecepcionPaquete(self, sucursal: int=None, puntoventa: int=None, documentoSector: int=None, tipoFactura: int=None,
                                   codigoRecepcion=None, test=None, esBot=None):
        if self.sd_factura_online_id.verificar_grupo_admin():
            fact_online = self.sd_factura_online_id
            cfg = fact_online.getConfig(fact_online.sd_codigo_modalidad, fact_online.sd_codigo_ambiente,
                                        fact_online.sd_codigo_sistema,
                                        fact_online.sd_nombre_sistema, fact_online.sd_nit_em,
                                        fact_online.sd_nombre_company, fact_online.sd_tipo_sistema, fact_online.sd_token)
            sucursal = sucursal or fact_online.sd_codigo_sucursal
            puntoventa = puntoventa or self.sd_factura_online_id.sd_codigo_punto_venta.sd_codigo_punto_venta if self.sd_factura_online_id.sd_es_punto_venta else 0
            codigoRecepcion = codigoRecepcion or self.sd_codigo_recepcion_paquetes
            tipoFactura = tipoFactura or self.sd_tipo_factura
            # print('codigo_sector', type(self.sd_codigo_documento_sector),self.sd_codigo_documento_sector)
            documentoSector = documentoSector or int(self.sd_codigo_documento_sector)
            service = ServiceFacturacionComputarizada() if int(self.sd_factura_online_id.sd_codigo_modalidad )== 2 else ServiceFacturacionElectronica()
            service.setConfig(cfg)
            service.cuis = self.sd_factura_online_id.sd_cuis
            service.cufd = self.sd_factura_online_id.sd_cufd
            res = service.validacionRecepcionPaqueteFactura(sucursal, puntoventa, codigoRecepcion, tipoFactura,
                                                            documentoSector)
            print('validacion paquetes', res)

            if res:
                if res['codigoDescripcion'] == 'VALIDADA':
                    self.write({
                        'state': 'validate'
                    })
                    # if not esBot:
                        # i = 0
                        # for invoice in self.sd_invoice_ids:
                            # fact_cuf = FacturasCuf[i]
                            # invoice.write({
                            #     'sd_nro_factura_siat': fact_cuf.cabecera.numeroFactura
                            # })
                            # invoice.action_post()

                        # for factura in FacturasCuf:
                        #     print(factura.cabecera.cuf)
                        #     url = 'https://pilotosiat.impuestos.gob.bo/consulta/QR?nit={0}&cuf={1}&numero={2}&t=1'.format(
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
                        mjs = fact_online.mensaje_personalizador('Validación de paquetes éxitosa.')
                        return mjs
                else:
                    if test or not esBot:
                        mensaje = ''
                        for mensaje_diccionario in res['mensajesList']:
                            mensaje = mensaje + mensaje_diccionario['descripcion'] + '\n'
                        print(mensaje)
                        # raise UserError(_('Observada: \n "%s"')%(mensaje))
            else:
                raise UserError(_('Hubo un error inesperado, por favor verifique su conexión a internet y vuelva a intentar.\n Consulte a su soporte si intento lo anterio'))
            return res

    def recepcionPaqueteFactura(self, cfg, facturas: list, codigoControlAntiguo, tipoFactura, evento,
                                cafc=None):
        if self.sd_factura_online_id.verificar_grupo_admin():
            service = ServiceFacturacionComputarizada() if int(self.sd_factura_online_id.sd_codigo_modalidad )== 2 else ServiceFacturacionElectronica()
            service.setConfig(cfg)
            service.cuis = self.sd_factura_online_id.sd_cuis
            service.cufd = self.sd_factura_online_id.sd_cufd
            # print('cufd de paquete', service.cufd)
            service.codigoControl = codigoControlAntiguo  # resCufd['codigoControl']

            res = service.recepcionPaqueteFactura(
                facturas,
                int(evento.sd_codigo_recepcion_evento_significativo),
                constants.TIPO_EMISION_OFFLINE,
                int(tipoFactura),
                cafc=cafc
            )
            return res
    def get_cafc(self):
        if self.sd_cafc:
            return str(self.sd_cafc)
        else:
            return None

    def publicar_facturas(self):
        if self.sd_invoice_ids:
            i=1
            for invoice in self.sd_invoice_ids:
                # print('fACTURA------------------------------', i)

                # print(invoice.sd_fecha_emision)
                if invoice.state == 'draft':
                    invoice.update({'sd_fecha_emision': self.sd_fecha_inicio})
                    invoice.post()
                    i += 1

    def validar_campos_necesarios(self):
        if not self.sd_cufd_id:
            raise UserError(_('Es necesario el campo Cufd para continuar'))
        if not self.name:
            raise UserError(_('Es necesario el campo Nombre para continuar'))
        if not self.sd_factura_online_id:
            raise UserError(_('Es necesario el campo Factura en Linea para continuar'))
        if not self.sd_cuis:
            raise UserError(_('Es necesario el campo Cuis para continuar'))
        # if not self.sd_cufd_id:
        #     raise UserError(_('Es necesario el campo Cufd para continuar'))
        if not self.sd_fecha_inicio:
            raise UserError(_('Es necesario el campo Fecha de Inicio para continuar'))
        if not self.sd_fecha_fin:
            raise UserError(_('Es necesario el campo Fecha Fin para continuar'))
        if not self.sd_evento_id:
            raise UserError(_('Es necesario el campo Contigencia para continuar'))
        if not self.sd_codigoControlAntiguo:
            raise UserError(_('Es necesario el campo Código control para continuar'))
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

