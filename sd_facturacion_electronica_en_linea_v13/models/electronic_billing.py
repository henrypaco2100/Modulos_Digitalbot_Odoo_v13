from odoo import api, fields, models, _
from suds.client import Client
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from datetime import datetime
class SdElectronicBilling(models.Model):
    _name = 'electronic.billing'
    _check_company_auto = True
    # FACTURACION ELECTRONICA Henry
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open','Abierto'),
        ('cuis', 'CUIS'),
        ('sicronizacion_cat', 'Sincronizacion de Catalogo'),
        ('cufd', 'CUFD'),
    ], string='Estado',default='draft' )
    name = fields.Char(readonly=True, default=lambda self: _('New'))
    start_date=fields.Datetime(string='Fecha inicial',default=fields.Datetime.now,readonly=True)

    @api.model
    def _diario_venta_disponible(self):
        account_journal_ids = self.env['account.journal'].search([('type', '=', 'sale'),('fcb_es_electronico','=',False)])
        if account_journal_ids:
            return account_journal_ids.mapped('id')
        else:
            return []

    sd_journal_id = fields.Many2one('account.journal', string='Diario',domain=lambda self: [('id', 'in', self._diario_venta_disponible())])

    company_id = fields.Many2one('res.company','Compañia',required=True, index=True, default=lambda self: self.env.company)
    sd_follow_line = fields.One2many('electronic.billing.follow', 'sd_facturacion_electronica_id', string='Seguimiento')

    # Campos Entrada/ Fields in
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
                                            ('2', 'Comptarizada en Linea'), ],
                                           string='Codigo Modalidad',
                                           default='1', readonly=1)
    sd_codigo_sucursal = fields.Selection([('0', 'Casa Matriz'),
                                           ('1', 'Sucursal 1'), ], default='0', string='Codigo Sucursal',
                                          help="Valor que identifica la sucursal donde se realiza la emisión de la Factura"
                                               "0 para Casa Matriz y 1,2,3 etc para sucursal")
    sd_es_punto_venta = fields.Boolean(string='es punto de venta', )
    sd_codigo_punto_venta = fields.Char(string="Codigo Punto Venta")
    sd_token = fields.Text(string="Token Delegado")
    # Campos salida / Fields out
    sd_cuis = fields.Char(string="CUIS",readonly=True)
    sd_cufd = fields.Char("CUF", help="Codigo unico de Facturacion de Impuesto Nacionales",readonly=True)
    sd_fecha_vigencia_cuis = fields.Datetime(string='Fecha Vigencia Cuis',readonly=True)
    sd_fecha_vigencia_cufd = fields.Datetime(string='Fecha Vigencia Cufd',readonly=True)
    sd_codigo_control = fields.Char(string='Codigo de Control',readonly=True)
    sd_direccion = fields.Char(string='Direccion',readonly=True)

    def confirmar_facturacion_electronica(self):
        if self.sd_journal_id:
            if self.sd_journal_id.fcb_es_electronico == False:
                self.write({
                    'state':'open'
                })
                self.sd_journal_id.write({
                    'fcb_es_electronico':True
                })
            else:
                raise AccessError(_('El Diario "%s" tiene una factura electronica en linea\n '
                                    'Elege otro Diario o comuniquese con su soporte porfavor.')%(self.sd_journal_id.name))
        else:
            raise AccessError(_("¡¡El Diario es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))

    def solicitudCuis(self):
        # codido sistema : 6D0A63102DD371B42D430FE
        # nit emisor : 8001727010
        # "codigoModalidad": 1,
        # "codigoSucursal": 0,
        # "codigoPuntoVenta": 0
        # token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJkaWVnbzIwMTIiLCJjb2RpZ29TaXN0ZW1hIjoiNkQwQTYzMTAyREQzNzFCNDJENDMwRkUiLCJuaXQiOiJINHNJQUFBQUFBQUFBTE13TURBME56STNNRFFBQUpaWnkxWUtBQUFBIiwiaWQiOjE1OTAyNywiZXhwIjoxNjQzNTg3MjAwLCJpYXQiOjE2MzY4MTE4MDksIm5pdERlbGVnYWRvIjo4MDAxNzI3MDEwLCJzdWJzaXN0ZW1hIjoiU0ZFIn0.x2ejUx0SvWM8Kl2m7jsF7sdB4PCdmbdJm_7ucbMOAjO_Z4k6po3kRE5segb0UFAy75Sf7GfLaS1bQZlzNTHBAQ
        url = 'https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionCodigos?wsdl'
        cliente = Client(url)
        self.validar_datos_para_Cuis()
        pToken = self.sd_token
        cliente.set_options(headers={'apikey': 'TokenApi ' + pToken})
        #VerificarComunicacion
        verificar_comunicacion = cliente.service.verificarComunicacion()
        self.save_mensajes_siat(verificar_comunicacion)
        print(cliente)
        print('paso 1 ', verificar_comunicacion)

        #Solicitar Cuis
        solicitudCuis = {
            "codigoAmbiente": int(self.sd_codigo_ambiente),
            "codigoSistema": self.sd_codigo_sistema,
            "nit": int(self.sd_nit_em),
            "codigoModalidad": int(self.sd_codigo_modalidad),
            "codigoSucursal": int(self.sd_codigo_sucursal),
            "codigoPuntoVenta": int(self.sd_codigo_punto_venta) if self.sd_es_punto_venta == 'False' else 0
        }
        resultado = cliente.service.cuis(solicitudCuis)
        print("2do paso", resultado)
        codigo_cuis = resultado['codigo']
        fecha_vigencia = resultado['fechaVigencia']
        if codigo_cuis and fecha_vigencia:
            new_date_str = fecha_vigencia.strftime("%m/%d/%Y %H:%M:%S")
            new_date = datetime.strptime(new_date_str,"%m/%d/%Y %H:%M:%S")
            self.write({
                'sd_cuis':codigo_cuis,
                'sd_fecha_vigencia_cuis':new_date,
            })
        self.save_mensajes_siat(resultado)
        self.verificar_cuis()
    def solicitudCufd(self):
        url = 'https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionCodigos?wsdl'
        cliente = Client(url)
        self.validar_datos_para_Cufd()
        pToken = self.sd_token
        cliente.set_options(headers={'apikey': 'TokenApi ' + pToken})
        #VerificarComunicacion
        verificar_comunicacion = cliente.service.verificarComunicacion()
        self.save_mensajes_siat(verificar_comunicacion)
        print(cliente)
        print('paso 1 ', verificar_comunicacion)

        #Solicitar Cuis
        solicitudCufd = {
            "codigoAmbiente": int(self.sd_codigo_ambiente),
            "codigoSistema": self.sd_codigo_sistema,
            "nit": int(self.sd_nit_em),
            "codigoModalidad": int(self.sd_codigo_modalidad),
            'cuis':self.sd_cuis,
            "codigoSucursal": int(self.sd_codigo_sucursal),
            "codigoPuntoVenta": int(self.sd_codigo_punto_venta) if self.sd_es_punto_venta == 'False' else 0
        }
        resultado = cliente.service.cufd(solicitudCufd)
        print("2do paso cufd", resultado)
        codigo_cufd = resultado['codigo']
        fecha_vigencia = resultado['fechaVigencia']
        codigo_control = resultado['codigoControl']
        direccion = resultado['direccion']
        if codigo_cufd and fecha_vigencia:
            new_date_str = fecha_vigencia.strftime("%m/%d/%Y %H:%M:%S")
            new_date = datetime.strptime(new_date_str,"%m/%d/%Y %H:%M:%S")
            self.write({
                'sd_cufd':codigo_cufd,
                'sd_fecha_vigencia_cufd':new_date,
                'sd_codigo_control':codigo_control,
                'sd_direccion' : direccion,
            })
            self.save_mensajes_siat_cufd(resultado)
            self.verificar_cufd()
    def verificar_cufd(self):
        if self.sd_cufd and self.sd_fecha_vigencia_cufd:
            self.sd_journal_id.write({
                'sd_cufd': self.sd_cufd,
                'sd_fecha_vigencia_cufd': self.sd_fecha_vigencia_cufd,
            })
            self.write({
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
            else:
                self.validar_caracter_numerico(self.sd_codigo_punto_venta, 'Codigo Punto Venta')
        if not self.sd_token:
            raise AccessError(_("¡¡El Token Delegado es Necesario!!\n "
                                "Porfavor Asegurese de haber rellenado el formulario correctamente."))
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
            else:
                self.validar_caracter_numerico(self.sd_codigo_punto_venta, 'Codigo Punto Venta')
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
            vals['name'] = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.today()).next_by_code('electronic.billing')
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

    @api.onchange('sd_codigo_punto_venta')
    def Control_de_nit_numerico(self):
        caracteres = self.sd_codigo_punto_venta
        diccionario_numerico = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
        if caracteres:
            for i in caracteres:
                if not i in diccionario_numerico:
                    self.sd_codigo_punto_venta = ''
                    return {
                        'warning': {
                            'message': _(
                                f'Se permiten solo caracteres numérico en el campo: "Codigo Punto Venta", porfavor vuelva a intentarlo!!. ')
                        }
                    }
    def sincronizacioncatalogos(self):
        url = 'https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionSincronizacion?wsdl'
        cliente = Client(url)
        # self.validar_datos_para_Cufd()
        pToken = self.sd_token
        cliente.set_options(headers={'apikey': 'TokenApi ' + pToken})
        print('sicronicacion ',cliente)

class SdElectronicBillingFollow(models.Model):
    _name = 'electronic.billing.follow'
    _description = 'lineas de seguimientos de mensajes facturacion electronica Siat'
    sd_facturacion_electronica_id = fields.Many2one('electronic.billing', string='Seguimiento de mensaje de respuesta SIAT')
    sd_mensaje = fields.Char(string='Mensajes')
    sd_codigo = fields.Integer(string='Codigo')
    sd_date_solicitud = fields.Datetime(string='fecha solicitud',default=fields.Datetime.now)
    sd_transaccion = fields.Boolean(string='Transaccion')