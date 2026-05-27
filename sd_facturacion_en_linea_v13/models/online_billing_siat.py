from odoo import api, fields, models, _
# from suds.client import Client
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from datetime import datetime, timedelta, time
import pytz
from pysiat.services.service_codigos import ServiceCodigos
import time
import platform
from pysiat import constants
from pysiat.services.service_sincronizacion import ServiceSincronizacion
from pysiat.classes.siat_exception import SiatException
from pysiat.services import service_operaciones

# Nit:452544024
# Usuario: Sodigital22
# Contraseña: Sodigitalim8001
# eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJTb2RpZ2l0YWwyMiIsImNvZGlnb1Npc3RlbWEiOiI3MjFCRUZENTA0OUMwODVERjUyRUFBRiIsIm5pdCI6Ikg0c0lBQUFBQUFBQUFETXhOVEkxTVRFd01nRUE2TTcxOEFrQUFBQT0iLCJpZCI6MzAxNDc0MiwiZXhwIjoxNjYzNjMyMDAwLCJpYXQiOjE2NTgzMzMxNTgsIm5pdERlbGVnYWRvIjo0NTI1NDQwMjQsInN1YnNpc3RlbWEiOiJTRkUifQ.1UxD-i7X8UW5M_B-is7SvwkwUZGqn2ZPu4PQdm-KrBIew2Sad8v-ZcqoQMn2JjrzkVliuvHzuP1qG0bZVo83RQ
# eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJTb2RpZ2l0YWwyMiIsImNvZGlnb1Npc3RlbWEiOiI3MjFCRUZENTA0OUMwODVERjUyRUFBRiIsIm5pdCI6Ikg0c0lBQUFBQUFBQUFETXhOVEkxTVRFd01nRUE2TTcxOEFrQUFBQT0iLCJpZCI6MzAxNDc0MiwiZXhwIjoxNjY2MjI0MDAwLCJpYXQiOjE2NjM2ODE3NDAsIm5pdERlbGVnYWRvIjo0NTI1NDQwMjQsInN1YnNpc3RlbWEiOiJTRkUifQ.xPn6JeOeBe7EAvkS6DAmauw4HA2-1B6fILQwFMk5Lg3jL7Uhvq-5pDOgesSpDqNPp5FJS8GxG8W1zBajOA1w-Q
ContadorConexion = 0
class SdElectronicBilling(models.Model):
    _name = 'online.billing.siat'
    # electronic.billing
    _check_company_auto = True
    # FACTURACION ELECTRONICA Henry
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open','Abierto'),
        ('cuis', 'CUIS'),
        ('sicronizacion_cat', 'Sincronizacion de Catalogo'),
        ('cufd', 'Confirmada'),
    ], string='Estado',default='draft')
    name = fields.Char(default=lambda self: _('New'))
    start_date = fields.Datetime(string='Fecha inicial',default=fields.Datetime.now,readonly=True)
    sd_municipio = fields.Char(string="Municipio")
    sd_nro_factura = fields.Integer(related='sd_journal_id.fcb_siguiente_Numero', string="Numero Factura")
    sd_factura_online_padre = fields.Many2one('online.billing.siat','Factura Padre')
    sd_multiple_linea_pdf = fields.Boolean('Multiples lineas')
    @api.model
    def _diario_venta_disponible(self):
        account_journal_ids = self.env['account.journal'].search([('type', '=', 'sale'),('fcb_es_electronico','=',False)])
        if account_journal_ids:
            return account_journal_ids.mapped('id')
        else:
            return []

    @api.model
    def _tipo_estado_resultado(self):
        # print('factura online', self.sd_factura_online_padre)
        reportes = self.env['punto.venta.factura'].search([('sd_factura_online_id', '=', 1)])
        # print('reportes,', reportes)

        if reportes:
            return reportes.mapped('id')
        else:
            return []
    
    @api.model
    def get_selection_field(self, model):
        # indices string puede ser integer
        docs = self.env[model].sudo().search([])
        res = []
        for doc in docs:
            res.append((str(doc.sd_codigo_clasificador), str(doc.sd_descripcion)))
        return res
    @api.model
    def _planilla_pdf(self):
        planillas_ids = self.env['ir.actions.report'].search([('report_type','=','qweb-pdf'),('model','=','account.move')])
        # print(planillas_ids,'----------------')
        if planillas_ids:
            return planillas_ids.mapped('id')
        else:
            return []

    sd_pantilla_pdf_id = fields.Many2one('ir.actions.report', string="Plantilla",
                                         domain=lambda self: [('id', 'in', self._planilla_pdf())])
    sd_es_enviar_correo = fields.Boolean('Envio de correo', default=True)
    sd_journal_id = fields.Many2one('account.journal', string='Diario',domain=lambda self: [('id', 'in', self._diario_venta_disponible())], copy=False)

    company_id = fields.Many2one('res.company','Compañia',required=True, index=True, default=lambda self: self.env.company)
    #campos de la compañia
    sd_nombre_company = fields.Char('Razon Social Emisor')
    sd_nro_company = fields.Char('Telefono Emisor   ')
    #campos de seguimiento
    sd_follow_line = fields.One2many('online.billing.siat.follow', 'sd_facturacion_electronica_id', string='Seguimiento', copy=False)
    #campos cufds list
    sd_cufd_ids = fields.One2many('factura.cufd', 'sd_facturacion_online_id', string="Cufd", copy=False)
    # Campos Entrada/ Fields in

    sd_nombre_sistema = fields.Char(string='Nombre del sistema')
    sd_tipo_sistema = fields.Selection([('PROVEEDOR', 'Proveedor'),
                                        ('PROPIO', 'Propio')
                                        ], default='PROVEEDOR', string='Tipo de sistema',
                                       )

    sd_codigo_actividad_id = fields.Many2one('factura.actividades', string="Codigo Actividad")
    sd_codigo_ambiente = fields.Selection([('1', 'Produccion'),
                                           ('2', 'Pruebas y Piloto'), ],
                                          string='Codigo Ambiente',
                                          default='2')

    fcb_tipo_factura_electronica = fields.Selection([('0', 'Ninguna'),
                                                     ('1', 'Compra y Venta'),
                                                     ('2', 'Alquiler Bienes Inmuebles'),
                                                     ('3', 'Comercial Exportacion'),
                                                     ('4', 'Comercial de Exportación en Libre Consignación'),
                                                     ('5', 'Venta en Zona Franca'),
                                                     ('6', 'Servicios Turisticos y Hospedaje'),
                                                     ('7', 'Seguridad Alimentaria y Abastecimiento'),
                                                     ('8', 'Tasa Cero'),
                                                     ('9', 'Compra y Venta Moneda Extranjera'),
                                                     ('10', 'Dutty Free'),
                                                     ('11', 'Sector Educativo'),
                                                     ('12', 'Comercializacion de Hidrocarburos'),
                                                     ('13', 'Hoteleria'),
                                                     ('14', 'Hospital Clinicas'), ],
                                                    string='Tipo de Factura Electronica a Emitir',
                                                    default='0')
    # cufd_id = fields.Char("CUFD", help="Codigo unico de Facturacion Diaria de Impuestos Nacionales")
    sd_codigo_sistema = fields.Char(string="Codigo Sistema")
    sd_nit_em = fields.Char(string="Nit Emisor")
    sd_codigo_modalidad = fields.Selection([('1', 'Electronica en Linea'),
                                            ('2', 'Computarizada en Linea'), ],
                                           string='Codigo Modalidad',
                                           default='1')
    sd_tipo_emision = fields.Selection(selection=lambda self: self.get_selection_field('tipo.emision.siat'),
                                       string='Tipo emision')

    sd_codigo_documento_sector = fields.Selection(selection=lambda self: self.get_selection_field('tipo.documento.sector.siat'),
                                                  string='Tipo Documento sector')

    sd_tipo_factura = fields.Selection(selection=lambda self: self.get_selection_field('tipo.factura.siat'),
                                       string='Tipo factura')

    sd_codigo_metodo_pago = fields.Selection(selection=lambda self: self.get_selection_field('metodo.pago.siat'),
                                             string='Método de Pago')

    sd_codigo_sucursal = fields.Selection(selection=lambda self: self.get_selection_field('sucursal.factura.siat'),
                                             string='Código Sucursal')
    sd_es_punto_venta = fields.Boolean(string='es punto de venta', )

    sd_codigo_punto_venta = fields.Many2one('punto.venta.factura', string='Código punto Venta',
                                            domain="[('sd_factura_online_id', '=', sd_factura_online_padre)]")
    sd_token = fields.Text(string="Token Delegado")
    # Campos salida / Fields out
    sd_cuis = fields.Char(string="CUIS",readonly=True, copy=False)
    sd_cufd = fields.Char("CUFD", help="Codigo unico de Facturacion de Impuesto Nacionales",readonly=True, copy=False)
    sd_fecha_vigencia_cuis = fields.Datetime(string='Fecha Vigencia Cuis',readonly=True, copy=False)
    sd_fecha_vigencia_cufd = fields.Datetime(string='Fecha Vigencia Cufd',readonly=True, copy=False)
    sd_codigo_control = fields.Char(string='Codigo de Control',readonly=True, copy=False)
    sd_direccion = fields.Char(string='Direccion',readonly=True, copy=False)
    # Evento significativo actual
    sd_evento_id = fields.Many2one('eventos.significativos.siat',string='Evento significativo')
    sd_name_evento = fields.Char(related='sd_evento_id.name')
    sd_codigo_recepcion_evento = fields.Char(related='sd_evento_id.sd_codigo_recepcion_evento_significativo')
    sd_contingencia_evento = fields.Many2one('mensaje.eventos.siat', related='sd_evento_id.sd_evento_id')
    sd_cufd_evento_id = fields.Many2one('factura.cufd', related='sd_evento_id.sd_cufd_id')
    sd_cufd_evento_string = fields.Char(related='sd_evento_id.sd_cufd_antiguo')
    sd_fecha_evento_ini = fields.Char(related='sd_evento_id.sd_fecha_ini')
    sd_fecha_evento_inicio = fields.Datetime(related='sd_evento_id.sd_fecha_inicio')
    sd_fecha_evento_fin = fields.Datetime(related='sd_evento_id.sd_fecha_fin')
    #otros
    sd_contador_conexion = fields.Integer('Contador conexion', default=0)
    sd_cambiar_endpoint = fields.Boolean('cambiar endpoint', default=False)
    sd_servidor_correo = fields.Many2one('ir.mail_server', string='Correo')
    sd_correo_respuesta = fields.Char('Correo de Respuesta')
    # ---------------certificado factura electronica-----------
    public_cert_filename = fields.Char(string='Nombre Certificado Publico')
    private_cert_filename = fields.Char(string='Nombre Certificado Privado')

    # token sodigitalim
    # eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJTb2RpZ2l0YWwyMiIsImNvZGlnb1Npc3RlbWEiOiI3MjFCRUZENTA0OUMwODVERjUyRUFBRiIsIm5pdCI6Ikg0c0lBQUFBQUFBQUFETXhOVEkxTVRFd01nRUE2TTcxOEFrQUFBQT0iLCJpZCI6MzAxNDc0MiwiZXhwIjoxNjYzNjMyMDAwLCJpYXQiOjE2NTgzMzMxNTgsIm5pdERlbGVnYWRvIjo0NTI1NDQwMjQsInN1YnNpc3RlbWEiOiJTRkUifQ.1UxD-i7X8UW5M_B-is7SvwkwUZGqn2ZPu4PQdm-KrBIew2Sad8v-ZcqoQMn2JjrzkVliuvHzuP1qG0bZVo83RQ

    def get_cert_paths(self):
        public = self.public_cert_filename + '.pem'
        private = self.private_cert_filename + '.pem'
        public_cert_path = '/{}/{}'.format(constants.DIRECCION, public)
        private_cert_path = '/{}/{}'.format(constants.DIRECCION, private)
        return public_cert_path, private_cert_path
    def verificar_nit_valido(self, nit_a_verificar):
        cfg = self.getConfig(self.sd_codigo_modalidad, self.sd_codigo_ambiente, self.sd_codigo_sistema,
                             self.sd_nombre_sistema, self.sd_nit_em,
                             self.sd_nombre_company, self.sd_tipo_sistema, self.sd_token)
        serviceCods = ServiceCodigos()
        serviceCods.setConfig(cfg)
        # Solicitar Cuis
        Data = [{
             "codigoAmbiente": int(self.sd_codigo_ambiente),
             "codigoSistema": self.sd_codigo_sistema,
             "nit": int(self.sd_nit_em),
             "codigoModalidad": int(self.sd_codigo_modalidad),
             "codigoSucursal": int(self.sd_codigo_sucursal),
             "nitParaVerificacion": int(nit_a_verificar),
             "cuis": self.sd_cuis
        }]
        res = serviceCods.verificarNit(Data)
        # print(res)
        return res

    def confirmar_facturacion_electronica(self):
        if self.sd_journal_id:
            if self.sd_journal_id.fcb_es_electronico == False:
                self.write({
                    'state': 'open'
                })
                self.sd_journal_id.write({
                    'fcb_es_electronico': True,
                    'sd_factura_online_id': self.id
                })
            else:
                raise AccessError(_('El Diario "%s" tiene una factura electronica en linea\n '
                                    'Elege otro Diario o comuniquese con su soporte porfavor.')%(self.sd_journal_id.name))
        else:
            raise AccessError(_("¡¡El Diario es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))

    def getConfig(self, modalidad=None, ambiente=None, codigoSistema=None, nombreSistema=None, nit=None, razonSocial=None,
                  tipo=None, token=None, ):
        # print('direccion', constants.DIRECCION)
        public, private = self.get_cert_paths()
        cfg = {
            'modalidad': int(modalidad) or constants.MOD_COMPUTARIZADA_ENLINEA,
            # 'modalidad': constants.MOD_ELECTRONICA_ENLINEA,
            'ambiente': int(ambiente) or constants.AMBIENTE_PRUEBAS,
            'codigoSistema': codigoSistema or '',
            'nombreSistema': nombreSistema or '',
            'nit': int(nit) or '',
            'razonSocial': razonSocial or '',
            'tipo': tipo or 'PROVEEDOR',
            'token': token,
            'pubCert': public,
            'privCert': private
        }
        print(cfg['pubCert'], cfg['privCert'])
        # '/{0}/{1}'.format(constants.DIRECCION, 'publickeysiat.pem')
        # '/{0}/{1}'.format(constants.DIRECCION, 'privatekeysiat.pem')
        return cfg

    def existe_cuis(self, fecha_factura=None):
        if self.sd_cuis:
            fecha_backend = self.obtener_fecha_backend(self.sd_fecha_vigencia_cuis)
            if not fecha_backend > (fecha_factura or datetime.now()):
                raise AccessError(_('Expiro la vigencia de Cuis esta vencido. Comuniquese con su soporte\nNo es posible continuar '))
            return True
        else:
            return False
    def solicitudCuis(self, test=None):
        # token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJBbGV4aW1wMjAxNyIsImNvZGlnb1Npc3RlbWEiOiI3MjBGN0Q0MUMyM0JGQTFCMkQzRjgwRSIsIm5pdCI6Ikg0c0lBQUFBQUFBQUFETzFOREEzTlRFeE1EUUNBQzdMZFZJS0FBQUEiLCJpZCI6NjQyODY5LCJleHAiOjE2NTkyMjU2MDAsImlhdCI6MTY1NjUzMTA3Miwibml0RGVsZWdhZG8iOjU5MDc1NDQwMTIsInN1YnNpc3RlbWEiOiJTRkUifQ.CEsJyiAce4DDgac8m4jUjUS-wiqTsSmgqCIUgaPmg5-mih71k4eXk_dEWGqQEaTQNfMrZuLYdkF2lnRY8UvlEQ
        # url = 'https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionCodigos?wsdl'
        grupo_correcto = self.verificar_grupo_admin()
        if not self.existe_cuis() and grupo_correcto or test:
            self.validar_datos_para_Cuis()

            cfg = self.getConfig(self.sd_codigo_modalidad, self.sd_codigo_ambiente, self.sd_codigo_sistema, self.sd_nombre_sistema, self.sd_nit_em,
                                 self.sd_nombre_company, self.sd_tipo_sistema, self.sd_token)
            serviceCods = ServiceCodigos()
            serviceCods.setConfig(cfg)
            serviceCods.cuis = self.sd_cuis
            #Solicitar Cuis
            DataCuis = {

                "codigoAmbiente": int(self.sd_codigo_ambiente),
                "codigoSistema": self.sd_codigo_sistema,
                "nit": int(self.sd_nit_em),
                "codigoModalidad": int(self.sd_codigo_modalidad),
                "codigoSucursal": int(self.sd_codigo_sucursal),
                "codigoPuntoVenta": self.sd_codigo_punto_venta.sd_codigo_punto_venta if self.sd_es_punto_venta else 0
            }

            # resultado = cliente.service.cuis(solicitudCuis)
            resultado = serviceCods.getCuis(DataCuis)
            print('Respuesta cuis',resultado)
            if resultado:
                serviceCods.cuis = resultado['codigo']
                # print("2do paso", resultado)
                codigo_cuis = resultado['codigo']
                fecha_vigencia = resultado['fechaVigencia']
                if codigo_cuis and fecha_vigencia:
                    new_date = self.obtener_fecha_frontend(fecha_vigencia)
                    self.write({
                        'sd_cuis': codigo_cuis,
                        'sd_fecha_vigencia_cuis': new_date,
                    })
                self.save_mensajes_siat(resultado)
                self.verificar_cuis()
                if not test:
                    mjs = self.mensaje_personalizador('Cuis solicitado con éxito.'+str(resultado))
                    return mjs
            else:
                raise UserError(_('No se pudo obtener cuis.'))
        
        return self.sd_cuis

    def existe_cufd(self):
        sw = False
        cufd = self.sd_cufd_ids.obtener_vigente()
        if cufd:
            fecha_backend = self.obtener_fecha_backend(cufd.sd_fecha_vigencia)
            if fecha_backend > datetime.now() or fecha_backend == datetime:
                sw = True
        return sw

    def solicitudCufd(self, test=None):
        grupo_correcto = self.verificar_grupo_admin()
        grupo_usuario = self.verificar_grupo_user()
        if not self.existe_cufd() or test:
            if (grupo_correcto or grupo_usuario):
            # serviceSincronizacion = ServiceSincronizacion()
            # resComunicacion = serviceSincronizacion.verificarComunicacion()
            # print("1er paso Verificacion", resComunicacion)
            # Solicitar Cufd
                self.validar_datos_para_Cufd()
                cfg = self.getConfig(self.sd_codigo_modalidad, self.sd_codigo_ambiente, self.sd_codigo_sistema,
                                     self.sd_nombre_sistema, self.sd_nit_em,
                                     self.sd_nombre_company, self.sd_tipo_sistema, self.sd_token)

                serviceCods = ServiceCodigos()
                serviceCods.setConfig(cfg)
                serviceCods.cuis = self.sd_cuis
                DataCufd = {
                    "codigoAmbiente": int(self.sd_codigo_ambiente),
                    "codigoSistema": self.sd_codigo_sistema,
                    "nit": int(self.sd_nit_em),
                    "codigoModalidad": int(self.sd_codigo_modalidad),
                    "codigoSucursal": int(self.sd_codigo_sucursal),
                    "codigoPuntoVenta": self.sd_codigo_punto_venta.sd_codigo_punto_venta if self.sd_es_punto_venta else 0
                }
                resCufd = serviceCods.getCufd(DataCufd)
                if resCufd:
                    if resCufd['transaccion'] == False and resCufd['codigo'] is None:
                        msj = resCufd['mensajesList'][0]['descripcion']
                        raise UserError(_('Verifique sus datos. \n "%s"') % (msj))
                else:
                    raise UserError(_('No se pudo obtener el código cufd.\nComuniquese con su soporte.'))

                serviceCods.cufd = resCufd['codigo']

                # print("2do paso cufd", resCufd)
                codigo_cufd = resCufd['codigo']
                fecha_vigencia = resCufd['fechaVigencia']
                fecha_string = fecha_vigencia.strftime("%Y-%m-%d %H:%M:%S.%f%z")
                # print('fecha string cuf', fecha_string)
                codigo_control = resCufd['codigoControl']
                direccion = resCufd['direccion']
                if codigo_cufd and fecha_vigencia:
                    fecha_fron = self.obtener_fecha_frontend(fecha_vigencia)
                    if not codigo_cufd in [cufd.sd_cufd for cufd in self.sd_cufd_ids]:

                        res_cufd = self.env['factura.cufd'].create({
                            'sd_facturacion_online_id': self.id,
                            'sd_contador_factura': 0,
                            'sd_cufd': codigo_cufd,
                            'sd_fecha_vigencia': fecha_fron,
                            'sd_codigo_control': codigo_control,
                            'sd_direccion': direccion,
                            'sd_fecha_string': fecha_string
                        })
                        self.save_mensajes_siat_cufd(resCufd)
                        self.verificar_cufd(res_cufd)
                    else:
                        print('se repite')
                    if not test:
                        mjs = self.mensaje_personalizador('Cufd solicitado con éxito.')
                        return mjs
            else:
                raise UserError(_('No tiene permisos para realizar la siguiente acción'))

        else:
            if not test:
                mjs = self.mensaje_personalizador('Ya existe un cufd en vigencia')
                return mjs

    # def funcion_auxiliar(self):
    #     cufd = self.env['factura.cufd'].search([('sd_facturacion_online_id', '=', self.id)])
    #     self.verificar_cufd(cufd)


    def verificar_cufd(self, cufd):
        if cufd:
            self.write({
                'sd_cufd': cufd.sd_cufd,
                'sd_fecha_vigencia_cufd': cufd.sd_fecha_vigencia,
                'sd_codigo_control': cufd.sd_codigo_control,
                'sd_direccion': cufd.sd_direccion,
                'state': 'cufd'
            })


    def verificar_cuis(self):
        if self.sd_cuis and self.sd_fecha_vigencia_cuis:
            self.sd_journal_id.write({
                'sd_codigo_cuis': self.sd_cuis,
                'sd_fecha_vigencia_cuis': self.sd_fecha_vigencia_cuis,
            })
            self.write({
                'state': 'cuis'
            })
    def save_mensajes_siat_cufd(self,Respuesta):
        value={
            'codigo':None,
            'mensaje':'Cufd obtenido con Exito',
            'transaccion' : Respuesta['transaccion']
        }
        self.create_new_line_follow(value)
    def save_mensajes_siat(self,Respuesta):
        for mensaje in Respuesta['mensajesList']:
            value={
                'codigo':mensaje['codigo'],
                'mensaje':mensaje['descripcion'],
                'transaccion' : Respuesta['transaccion']
            }
            self.create_new_line_follow(value)
    def validar_datos_para_Cuis(self):
        if not self.sd_codigo_ambiente:
            raise AccessError(_("¡¡El Codigo Ambiente es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
        if not self.sd_codigo_sistema:
            raise AccessError(_("¡¡El Codigo del Sistema es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
        if not self.sd_nit_em:
            raise AccessError(_("¡¡El Nit Emisor es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
        else:
            self.validar_caracter_numerico(self.sd_nit_em, 'Nit Emisor')
        if not self.sd_codigo_modalidad:
            raise AccessError(_("¡¡El Codigo Modalidad es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
        if not self.sd_codigo_sucursal:
            raise AccessError(_("¡¡El Codigo Sucursal es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
        if self.sd_es_punto_venta:
            if not self.sd_codigo_punto_venta:
                raise AccessError(_("¡¡El Codigo Punto Venta es Necesario!!\n "
                                    "Porfavor Asegurese de haber rellenado el formulario correctamente."))

        # if not self.sd_token:
        #     raise AccessError(_("¡¡El Token Delegado es Necesario!!\n "
        #                         "Porfavor Asegurese de haber rellenado el formulario correctamente."))
    def validar_datos_para_Cufd(self):
        if not self.sd_codigo_ambiente:
            raise AccessError(_("¡¡El Codigo Ambiente es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
        if not self.sd_codigo_sistema:
            raise AccessError(_("¡¡El Codigo del Sistema es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
        if not self.sd_nit_em:
            raise AccessError(_("¡¡El Nit Emisor es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
        else:
            self.validar_caracter_numerico(self.sd_nit_em, 'Nit Emisor')
        if not self.sd_codigo_modalidad:
            raise AccessError(_("¡¡El Codigo Modalidad es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
        if not self.sd_codigo_sucursal:
            raise AccessError(_("¡¡El Codigo Sucursal es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
        if self.sd_es_punto_venta:
            if not self.sd_codigo_punto_venta:
                raise AccessError(_("¡¡El Codigo Punto Venta es Necesario!!\n "
                                    "Porfavor Asegurese de haber rellenado el formulario correctamente."))

        if not self.sd_token:
            raise AccessError(_("¡¡El Token Delegado es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
        if not self.sd_cuis:
            raise AccessError(_("¡¡El Cuis es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))

    def validar_caracter_numerico(self, caracteres, nombre_campo):
        diccionario_numerico = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
        if caracteres:
            for i in caracteres:
                if not i in diccionario_numerico:
                    raise AccessError(_('¡¡El Campo "%s" solo permite caracteres tipos numericos!!\n '
                                        'Porfavor Asegurese de haber rellenado el formulario correctamente.') % (
                                          nombre_campo))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.today()).next_by_code('online.billing.siat')
        res = super(SdElectronicBilling, self).create(vals)
        return res
    def create_new_line_follow(self,vals):
        values = ({
            'sd_facturacion_electronica_id': self.id,
            'sd_codigo':vals['codigo'] if vals['codigo'] else None,
            'sd_mensaje':vals['mensaje'] if vals['mensaje'] else None,
            'sd_transaccion' : vals['transaccion'] if vals['transaccion'] else None,
        })
        # self.env[self.computer_invoice_line_ids._name].new(values)
        self.env[self.sd_follow_line._name].create(values)

    @api.onchange('sd_nit_em')
    def Control_de_nit_numerico(self):
        caracteres = self.sd_nit_em
        diccionario_numerico = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
        if caracteres:
            for i in caracteres:
                if not i in diccionario_numerico:
                    self.sd_nit_em = ''
                    return {
                        'warning': {
                            'message': _(
                                f'Se permiten solo caracteres numérico en el campo: "Nit Emisor", porfavor vuelva a intentarlo!!. ')
                        }
                    }

    # @api.onchange('sd_codigo_punto_venta')
    # def Control_de_nit_numerico(self):
    #     caracteres = self.sd_codigo_punto_venta
    #     diccionario_numerico = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
    #     if caracteres:
    #         for i in caracteres:
    #             if not i in diccionario_numerico:
    #                 self.sd_codigo_punto_venta = ''
    #                 return {
    #                     'warning': {
    #                         'message': _(
    #                             f'Se permiten solo caracteres numérico en el campo: "Codigo Punto Venta", porfavor vuelva a intentarlo!!. ')
    #                     }
    #                 }
    #obtencion de fechas para coordinar hora backend

    def obtener_fecha_backend(self, fecha):
        return fecha - timedelta(hours=4)

    def obtener_fecha_frontend(self, fechaHora):
        if type(fechaHora) == type('str'):
            fechaHora = fechaHora.replace('T', ' ')
            # print('fecha string', fechaHora)
            # new_date_str = datetime.strftime("%m/%d/%Y %H:%M:%S")
            new_date = datetime.strptime(fechaHora, "%Y-%m-%d %H:%M:%S.%f")
            new_date_str = new_date.strftime("%Y/%m/%d %H:%M:%S")
            final_date = datetime.strptime(new_date_str, "%Y/%m/%d %H:%M:%S")
            # print('fecha_backend_sincro', final_date)
            # user_tz = self.env.user.tz
            # local = pytz.timezone(user_tz)
            # fecha_zona = (pytz.utc.localize(final_date).astimezone(local)).date()
            # hora = (pytz.utc.localize(final_date).astimezone(local)).time()
            # fecha_zona_bolivia = datetime.combine(fecha_zona,hora)
            # print(fecha_zona_bolivia, hora)
        else:
             new_date_str = fechaHora.strftime("%Y-%m-%d %H:%M:%S.%f")
             final_date = datetime.strptime(new_date_str, "%Y-%m-%d %H:%M:%S.%f")
        return final_date + timedelta(hours=4)

    # CIERRE DE SISTEMA
    def test_cierre_sistema(self):
        if self.verificar_grupo_admin():
            cfg = self.getConfig(self.sd_codigo_modalidad, self.sd_codigo_ambiente, self.sd_codigo_sistema,
                                 self.sd_nombre_sistema, self.sd_nit_em,
                                 self.sd_nombre_company, self.sd_tipo_sistema, self.sd_token)
            ServiceOperaciones = service_operaciones.ServiceOperaciones()
            ServiceOperaciones.setConfig(cfg)
            ServiceOperaciones.cuis = self.sd_cuis
            res = ServiceOperaciones.cierreOperacionesSistema(int(self.sd_codigo_sucursal), int(self.sd_codigo_punto_venta))
            self.save_mensajes_siat(res)
            print(res)
            if res['transaccion']:
                self.write({
                    'sd_cuis': '',
                    'sd_cufd': '',
                    'sd_fecha_vigencia_cuis': '',
                    'sd_fecha_vigencia_cufd': '',
                    'sd_codigo_control': '',
                    'sd_direccion': '',
                    'state': 'open'
                })
                mjs = self.mensaje_personalizador('Cierre de sistema exitoso.')
                return mjs
            else:
                mensaje = res['mensajesList'][0]['descripcion']
                raise UserError(_(mensaje))


    # SINCRONIZACION DE CATALOGOS
    def existeRes(self, elemento):
        if not elemento:
            raise UserError(_('Fallo la sincronizacion por favor comuniquese con su soporte '
                              '\n - Fallo los servidores de siat \n - Fallo la conexión'))
        else:
            return elemento

    # verificar comunicacion
    def verificar_comunicacion_siat(self):
        cfg = self.getConfig(self.sd_codigo_modalidad, self.sd_codigo_ambiente, self.sd_codigo_sistema,
                             self.sd_nombre_sistema, self.sd_nit_em,
                             self.sd_nombre_company, self.sd_tipo_sistema, self.sd_token)
        serviceSincronizacion = ServiceSincronizacion()
        serviceSincronizacion.setConfig(cfg)
        serviceSincronizacion.cuis = self.sd_cuis
        char = 'p' if self.sd_cambiar_endpoint else None
        resComunicacion = serviceSincronizacion.verificarComunicacion(endpoint=char)
        if resComunicacion:
            return True
        else:
            return False
    def ejecutar_todo_sincronizacion(self, sucursal, punto_venta, service):
        # res_comunicacion = service.verificarComunicacion()
        res_actividades = self.existeRes(service.sincronizarActividades(sucursal, punto_venta))
        # print('actividades', res_actividades)

        # res_fecha = service.sincronizarFechaHora(sucursal,punto_venta)
        res_tipo_punto_venta = self.existeRes(service.sincronizarParametricaTipoPuntoVenta(sucursal,punto_venta))
        res_tipo_emision = self.existeRes(service.sincronizarParametricaTipoEmision(sucursal, punto_venta))
        res_tipo_habitacion = self.existeRes(service.sincronizarParametricaTipoHabitacion(sucursal, punto_venta))
        res_acti_documento_sector = self.existeRes(service.sincronizarListaActividadesDocumentoSector(sucursal, punto_venta))
        res_leyenda_factura = self.existeRes(service.sincronizarListaLeyendasFactura(sucursal, punto_venta))
        res_mensajes_servicios = self.existeRes(service.sincronizarListaMensajesServicios(sucursal, punto_venta))
        res_productos_servicios = self.existeRes(service.sincronizarListaProductosServicios(sucursal,punto_venta))
        res_eventos_significativos = self.existeRes(service.sincronizarParametricaEventosSignificativos(sucursal, punto_venta))
        res_motivo_anulacion = self.existeRes(service.sincronizarParametricaMotivoAnulacion(sucursal, punto_venta))
        res_pais_origen = self.existeRes(service.sincronizarParametricaPaisOrigen(sucursal, punto_venta))
        res_documento_identidad = self.existeRes(service.sincronizarParametricaTipoDocumentoIdentidad(sucursal, punto_venta))
        res_tipo_metodo_pago = self.existeRes(service.sincronizarParametricaTipoMetodoPago(sucursal, punto_venta))
        res_tipo_documento_sector = self.existeRes(service.sincronizarParametricaTipoDocumentoSector(sucursal, punto_venta))
        res_tipo_moneda = self.existeRes(service.sincronizarParametricaTipoMoneda(sucursal, punto_venta))
        res_tipos_factura = self.existeRes(service.sincronizarParametricaTiposFactura(sucursal, punto_venta))
        res_unidad_medida = self.existeRes(service.sincronizarParametricaUnidadMedida(sucursal, punto_venta))

        result = {
            'actividades': res_actividades,
        #     'fecha_hora': res_fecha,
            'tipo_punto_venta': res_tipo_punto_venta,
            'tipo_emision': res_tipo_emision,
            'tipo_habitacion': res_tipo_habitacion,
            'actividad_documentos_sector': res_acti_documento_sector,
            'leyendas_factura': res_leyenda_factura,

            'mensajes_servicios': res_mensajes_servicios,
            'productos_servicios': res_productos_servicios,
            'eventos_significativos': res_eventos_significativos,
            'motivo_anulacion': res_motivo_anulacion,
            'pais_origen': res_pais_origen,
            'documento_identidad': res_documento_identidad,
            'tipo_metodo_pago': res_tipo_metodo_pago,
            'tipo_documento_sector': res_tipo_documento_sector,
            'tipo_moneda': res_tipo_moneda,
            'tipos_factura': res_tipos_factura,
            'unidad_medida': res_unidad_medida
        }
        return result

    def rellenarDict(self, dict):
        valor = {
            'sd_codigo_clasificador': dict['codigoClasificador'],
            'sd_descripcion': dict['descripcion']
        }
        return valor

    def verificar_repetidos(self, elemento,elementos, action, elementoadicional=None):
        sw = False
        for comparar in elementos:
            if action == 'actividad':
                if comparar.sd_codigo_caeb == elemento:
                    sw = True
            if action in ('mensaje', 'punto_venta','motivo_anulacion', 'tipo_emision',
                          'tipo_habitacion', 'pais_origen', 'doc_identidad', 'evento_significativo', 't_documento_sector',
                          'tipo_moneda', 'metodo_pago', 'tipo_factura', 'unidad_medida'):
                if str(comparar.sd_codigo_clasificador) == str(elemento):
                    sw = True
            if action == 'producto':
                if comparar.sd_codigo_actividad.sd_codigo_caeb == elemento and comparar.sd_codigo_producto == elementoadicional:
                    sw = True
            if action == 'actividad_doc':
                if comparar.sd_codigo_actividad_id.sd_codigo_caeb == elemento and comparar.sd_codigo_doc_sector_id.sd_codigo_clasificador == elementoadicional:
                    sw = True
            if action == 'leyenda_factura':
                if comparar.sd_codigo_actividad_id.sd_codigo_caeb == elemento and comparar.sd_descripcion_leyenda == elementoadicional:
                    sw = True
        return sw

    def creacionActividadesSiat(self, actividades):
        all_actividades = self.env['factura.actividades'].search([])
        for actividad in actividades:
            if not self.verificar_repetidos(actividad['codigoCaeb'], all_actividades, 'actividad'):
                valor = {
                    'sd_codigo_caeb': actividad['codigoCaeb'],
                    'sd_descripcion': actividad['descripcion'],
                    'sd_tipo_actividad': actividad['tipoActividad']
                }
                self.env['factura.actividades'].create(valor)

    def creacionActividadesDocumentoSiat(self, actividad_documentos):
        all_actividades_documentos = self.env['tipo.actividad.documento.siat'].search([])
        for actividad_doc in actividad_documentos:
            if not self.verificar_repetidos(actividad_doc['codigoActividad'], all_actividades_documentos,
                                            'actividad_doc', actividad_doc['codigoDocumentoSector']):
                actividad = self.env['factura.actividades'].search([('sd_codigo_caeb', '=', actividad_doc['codigoActividad'])])
                documento = self.env['tipo.documento.sector.siat'].search([('sd_codigo_clasificador', '=', actividad_doc['codigoDocumentoSector'])])
                valor = {
                    'sd_codigo_actividad_id': actividad.id,
                    'sd_codigo_doc_sector_id': documento.id,
                    'sd_tipo_doc_sector': actividad_doc['tipoDocumentoSector']
                }
                self.env['tipo.actividad.documento.siat'].create(valor)

    def creacionLeyendaFacturaSiat(self, leyenda_facturas):
        domain = self.domain_model_multicompany()
        all_leyendas = self.env['leyenda.factura.siat'].search(domain)
        print('leyendas', all_leyendas)
        for leyenda in leyenda_facturas:
            
            if not self.verificar_repetidos(leyenda['codigoActividad'], all_leyendas,
                                            'leyenda_factura', leyenda['descripcionLeyenda']):
                
                actividad = self.env['factura.actividades'].search([('sd_codigo_caeb', '=', leyenda['codigoActividad'])])

                valor = {
                    'sd_codigo_actividad_id': actividad.id,
                    'sd_descripcion_leyenda': leyenda['descripcionLeyenda']
                }
                # self.env['tipo.actividad.documento.siat'].create(valor)
                self.env['leyenda.factura.siat'].create(valor)


    def creacionProductosSiat(self, productos):
        domain = self.domain_model_multicompany()
        all_producto = self.env['product.service.siat'].search(domain)
        print('productos',all_producto)
        for producto in productos:
            if not self.verificar_repetidos(producto['codigoActividad'], all_producto, 'producto', str(producto['codigoProducto'])):
                actividad = self.env['factura.actividades'].search(
                    [('sd_codigo_caeb', '=', producto['codigoActividad'])])
                valor = {
                    'sd_codigo_actividad': actividad.id,
                    'sd_codigo_producto': producto['codigoProducto'],
                    'sd_descripcion_producto': producto['descripcionProducto'],
                }
                product_service_siat_id = self.env['product.service.siat'].create(valor)
                for nandina in producto['nandina']:
                    self.env['nandina.service.siat'].create(
                        {
                            'sd_product_id': product_service_siat_id.id,
                            'sd_codigo_nandina': nandina,
                        }
                    )

    def creacionModeloService(self, elementos, modelo, action):
        all_objetos = self.env[modelo].search([])
        if modelo == 'metodo.pago.siat':
            domain = self.domain_model_multicompany()
            all_objetos = self.env[modelo].search(domain)

        for elemento in elementos:
            if not self.verificar_repetidos(elemento['codigoClasificador'], all_objetos, action):
                valor = self.rellenarDict(elemento)
                self.env[modelo].create(valor)

    def sincronizacioncatalogos(self, test=None):
        grupo_admin = self.verificar_grupo_admin()
        if grupo_admin:
            cfg = self.getConfig(self.sd_codigo_modalidad, self.sd_codigo_ambiente, self.sd_codigo_sistema,
                                 self.sd_nombre_sistema, self.sd_nit_em,
                                 self.sd_nombre_company, self.sd_tipo_sistema, self.sd_token)
            service = ServiceSincronizacion()
            service.setConfig(cfg)
            service.cuis = self.sd_cuis
            punto_venta = self.sd_codigo_punto_venta.sd_codigo_punto_venta if self.sd_es_punto_venta else 0
            resEvents = self.ejecutar_todo_sincronizacion(int(self.sd_codigo_sucursal), punto_venta, service)

            actividades = resEvents['actividades']['listaActividades']
            mensajes = resEvents['mensajes_servicios']['listaCodigos']
            punto_ventas = resEvents['tipo_punto_venta']['listaCodigos']
            producto_servicio = resEvents['productos_servicios']['listaCodigos']
            motivo_anulacion = resEvents['motivo_anulacion']['listaCodigos']
            tipo_emision = resEvents['tipo_emision']['listaCodigos']
            tipo_habitacion = resEvents['tipo_habitacion']['listaCodigos']
            pais_origen = resEvents['pais_origen']['listaCodigos']
            documento_identidad = resEvents['documento_identidad']['listaCodigos']
            evento_significativo = resEvents['eventos_significativos']['listaCodigos']
            metodo_pago = resEvents['tipo_metodo_pago']['listaCodigos']
            tipo_documento = resEvents['tipo_documento_sector']['listaCodigos']
            tipo_moneda = resEvents['tipo_moneda']['listaCodigos']
            tipo_factura = resEvents['tipos_factura']['listaCodigos']
            unidad_medida = resEvents['unidad_medida']['listaCodigos']
            actividad_documentos = resEvents['actividad_documentos_sector']['listaActividadesDocumentoSector']
            leyenda_factura = resEvents['leyendas_factura']['listaLeyendas']

            self.creacionModeloService(mensajes, 'mensaje.service.siat', 'mensaje')
            self.creacionActividadesSiat(actividades)
            self.creacionModeloService(punto_ventas, 'punto.venta.siat', 'punto_venta')
            self.creacionProductosSiat(producto_servicio)
            self.creacionModeloService(motivo_anulacion, 'motivo.anulacion.siat', 'motivo_anulacion')
            self.creacionModeloService(tipo_emision, 'tipo.emision.siat', 'tipo_emision')
            self.creacionModeloService(tipo_habitacion, 'tipo.habitacion.siat', 'tipo_habitacion')
            self.creacionModeloService(pais_origen, 'pais.origen.siat', 'pais_origen')
            self.creacionModeloService(documento_identidad, 'documento.identidad.siat', 'doc_identidad')
            self.creacionModeloService(evento_significativo, 'mensaje.eventos.siat', 'evento_significativo')
            self.creacionModeloService(metodo_pago, 'metodo.pago.siat', 'metodo_pago')
            self.creacionModeloService(tipo_documento, 'tipo.documento.sector.siat', 't_documento_sector')
            self.creacionModeloService(tipo_moneda, 'tipo.moneda.siat', 'tipo_moneda')
            self.creacionModeloService(tipo_factura, 'tipo.factura.siat', 'tipo_factura')
            self.creacionModeloService(unidad_medida, 'unidad.medida.siat', 'unidad_medida')
            self.creacionActividadesDocumentoSiat(actividad_documentos)
            self.creacionLeyendaFacturaSiat(leyenda_factura)
            self.write({
                'state': 'sicronizacion_cat'
            })
            if not test:
                mjs = self.mensaje_personalizador('Sincronización de catálogos realizada con éxito.')
                return mjs


        # print('sicronicacion ', resEvents)

    def domain_model_multicompany(self):
        user = self.env.user
        # user.has_group('base.group_multi_company')
        if self.company_id:
            domain = [('company_id', '=', self.company_id.id)]
        elif len(self.env.user.company_ids) > 1:
            print('error tiene seleccionado multiples compañias')
            raise UserError(_('Por favor seleccione solo una compañia para realizar la sincronizacion de catalagos'))
        else:
            domain = [('company_id','=', self.env.user.company_ids.id)]
        return domain

    def action_registrar_evento(self):
        self.ensure_one()
        evento_id = self.env['eventos.significativos.siat'].sudo().create(
            {'sd_factura_online_id': self.id,
             'sd_cuis': self.sd_cuis,
             'sd_cufd_antiguo': self.sd_cufd,
             'sd_fecha_inicio': self.sd_fecha_vigencia_cufd,
             })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'eventos.significativos.siat',
            'view_mode': 'form',
            'views': [[self.env.ref('sd_facturacion_en_linea_v13.sd_form_mensaje_service_siat').id, 'form']],
            'res_id': evento_id.id,
            'target': 'current',
        }
    def action_registrar_emision_paquete(self):
        self.ensure_one()
        paquete_id = self.env['siat.emision.paquete.offline'].sudo().create(
            {'sd_factura_online_id':self.id,
             })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'siat.emision.paquete.offline',
            'view_mode': 'form',
            'views': [[self.env.ref('sd_facturacion_en_linea_v13.sd_form_emision_paquete_siat').id, 'form']],
            'res_id': paquete_id.id,
            'target': 'current',
        }
    #BUTTON BOX LISTA
    def action_list_view_eventos_significativos_siat(self):
        self.ensure_one()
        evento_ids = self.env['eventos.significativos.siat'].search([
            ('sd_factura_online_id', '=', self.id ),
        ])
        return {
            'name': _('Eventos Significativos'),
            'view_mode': 'tree,form',
            'res_model': 'eventos.significativos.siat',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', evento_ids.ids)],
        }
    def action_list_view_emision_paquetes_siat(self):
        # print('paquetes')
        self.ensure_one()
        paquete_ids = self.env['siat.emision.paquete.offline'].search([
            ('sd_factura_online_id', '=', self.id),
        ])
        return {
            'name': _('Emision de Paquetes'),
            'view_mode': 'tree,form',
            'res_model': 'siat.emision.paquete.offline',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', paquete_ids.ids)],
        }
    def action_list_view_factura_siat(self):
        self.ensure_one()
        factura_ids = self.env['account.move'].search([
            ('journal_id.sd_factura_online_id', '=', self.id),
        ])
        return {
            'name': _('Facturas '),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', factura_ids.ids)],
        }
    # Mensaje de confirmaciones

    def mensaje_personalizador(self, mensaje):

        message_id = self.env['sd.message.wizard'].create({'message': mensaje})
        return {
            'name': 'Proceso Exitoso!!',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sd.message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }
    
    #Verificacion de grupos
    def verificar_grupo_admin(self):
        admin = self.env['res.users'].has_group('sd_facturacion_en_linea_v13.sd_facturacion_electronica_en_linea_group')
        if not admin:
            if not self.verificar_grupo_user():
                raise UserError(_('No pertenece a un grupo con permisos para realizar la acción'))
        else:
            return admin

    def verificar_grupo_user(self):
        user = self.env['res.users'].has_group('sd_facturacion_en_linea_v13.sd_facturacion_electronica_en_linea_usuario_group')
        if not user:
            if not self.verificar_grupo_admin():
                raise UserError(_('No pertenece a un grupo con permisos para realizar la acción'))
            else:
                return user
        else:
            return user
        
    def verificar_grupo_anular(self):
        anular = self.env['res.users'].has_group('sd_facturacion_en_linea_v13.sd_anulacion_factura_group')
        if not anular:
            raise UserError(_('No pertenece a un grupo con permisos para realizar la acción'))
        else:
            return anular

#     funciones de test auxiliares
    def sincrotest(self, test=None):
        cfg = self.getConfig(self.sd_codigo_modalidad, self.sd_codigo_ambiente, self.sd_codigo_sistema,
                             self.sd_nombre_sistema, self.sd_nit_em,
                             self.sd_nombre_company, self.sd_tipo_sistema, self.sd_token)
        service = ServiceSincronizacion()
        service.setConfig(cfg)
        service.cuis = self.sd_cuis
        punto_venta = self.sd_codigo_punto_venta.sd_codigo_punto_venta if self.sd_es_punto_venta else 0
        resFecha = service.sincronizarFechaHora(int(self.sd_codigo_sucursal), punto_venta)
        resActividades = service.sincronizarActividades(int(self.sd_codigo_sucursal), punto_venta)
        resActividadDOcSector = service.sincronizarListaActividadesDocumentoSector(int(self.sd_codigo_sucursal), punto_venta)
        resleyenda = service.sincronizarListaLeyendasFactura(int(self.sd_codigo_sucursal), punto_venta)
        resmensajeServ = service.sincronizarListaMensajesServicios(int(self.sd_codigo_sucursal), punto_venta)
        resProdServ = service.sincronizarListaProductosServicios(int(self.sd_codigo_sucursal), punto_venta)
        time.sleep(1)
        reseveSIgn = service.sincronizarParametricaEventosSignificativos(int(self.sd_codigo_sucursal), punto_venta)
        resmo = service.sincronizarParametricaMotivoAnulacion(int(self.sd_codigo_sucursal), punto_venta)
        respaises = service.sincronizarParametricaPaisOrigen(int(self.sd_codigo_sucursal), punto_venta)
        restipoIden = self.existeRes(service.sincronizarParametricaTipoDocumentoIdentidad(int(self.sd_codigo_sucursal), punto_venta))
        # print(restipoIden)
        restipodocsector = service.sincronizarParametricaTipoDocumentoSector(int(self.sd_codigo_sucursal), punto_venta)
        restipoEmi = service.sincronizarParametricaTipoEmision(int(self.sd_codigo_sucursal), punto_venta)
        # time.sleep(2)
        retipohab = service.sincronizarParametricaTipoHabitacion(int(self.sd_codigo_sucursal), punto_venta)
        resmetodopago = service.sincronizarParametricaTipoMetodoPago(int(self.sd_codigo_sucursal), punto_venta)
        restipomoneda = service.sincronizarParametricaTipoMoneda(int(self.sd_codigo_sucursal), punto_venta)
        # time.sleep(2)
        restipopuntoventa = service.sincronizarParametricaTipoPuntoVenta(int(self.sd_codigo_sucursal), punto_venta)
        restipofactura = service.sincronizarParametricaTiposFactura(int(self.sd_codigo_sucursal), punto_venta)
        resunidadmedida = service.sincronizarParametricaUnidadMedida(int(self.sd_codigo_sucursal), punto_venta)




class SdElectronicBillingFollow(models.Model):
    _name = 'online.billing.siat.follow'
    _description = 'lineas de seguimientos de mensajes facturacion electronica Siat'
    sd_facturacion_electronica_id = fields.Many2one('online.billing.siat', string='Seguimiento de mensaje de respuesta SIAT')
    sd_mensaje = fields.Char(string='Mensajes')
    sd_codigo = fields.Integer(string='Codigo')
    sd_date_solicitud = fields.Datetime(string='fecha solicitud',default=fields.Datetime.now)
    sd_transaccion = fields.Boolean(string='Transaccion')

class SdCodigoUnicoFacturacionDiario(models.Model):
    _name = 'factura.cufd'
    _description = 'Codigo unico de facturacion diaria'
    _rec_name = 'sd_fecha_vigencia'

    sd_facturacion_online_id = fields.Many2one('online.billing.siat', string='Factura Online', readonly=True)
    # sd_facturacion_online_test_id = fields.Many2one('online.billing.siat', string='Factura test')
    sd_contador_factura = fields.Integer(string="Contador Factura", readonly=True)
    sd_cufd = fields.Char(string="Cufd", readonly=True)
    sd_fecha_vigencia = fields.Datetime(string="Fecha vigencia Cufd", readonly=True)
    sd_codigo_control = fields.Char(string="Codigo Control", readonly=True)
    sd_direccion = fields.Char(string="Dirección", readonly=True)
    sd_is_register = fields.Boolean(default=False, string='Registro Evento', readonly=True)
    sd_fecha_string = fields.Char(string='fecha string', readonly=True)
    def obtener_vigente(self):
        all_cufd = self.env['factura.cufd'].search([('sd_facturacion_online_id', '=', self.sd_facturacion_online_id.id),
                                                    ('sd_cufd', '=', self.sd_facturacion_online_id.sd_cufd)])

        return all_cufd