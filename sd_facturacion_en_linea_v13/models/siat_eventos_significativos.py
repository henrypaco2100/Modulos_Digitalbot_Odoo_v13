from odoo import api, fields, models, _
from pysiat.services.service_operaciones import ServiceOperaciones
from pysiat import functions
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class EventosSignificativosSiat(models.Model):
    _name = 'eventos.significativos.siat'

    name = fields.Char(string='Nombre')
    sd_factura_online_id = fields.Many2one('online.billing.siat', string='Factura en Linea', required=True)
    sd_cuis = fields.Char(related='sd_factura_online_id.sd_cuis', string='Cuis', readonly=True, required=True)
    sd_cufd_antiguo = fields.Char(related='sd_cufd_id.sd_cufd', string='Cufd Antiguo', readonly=True, required=True)
    sd_fecha_inicio = fields.Datetime(string='Fecha de Inicio', readonly=False)
    sd_fecha_ini = fields.Char(string='Fecha inicio')
    sd_fecha_fin = fields.Datetime(string='Fecha Fin')
    sd_evento_id = fields.Many2one('mensaje.eventos.siat', string='Contingencia')
    sd_codigo_recepcion_evento_significativo = fields.Char(string='Codigo Recepcion Evento significativo', readonly=True)
    sd_is_test = fields.Boolean('Es test', default=False)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('register', 'Registrado'),
    ], string='Estado', default='draft')
    # @api.model codigo =594738
    # def _tipo_estado_resultado(self):
    #     print('factura', self.sd_cufd_id.id)
    #     reportes = self.env['factura.cufd'].search([('sd_facturacion_online_id', '=', self.sd_factura_online_id.id)])
    #     print('reportes,', reportes)
    #
    #     if reportes:
    #         return reportes.mapped('id')
    #     else:
    #         return []

    sd_cufd_id = fields.Many2one('factura.cufd', string='Cufd',
                                 domain="[('sd_facturacion_online_id', '=', sd_factura_online_id)]")

    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)

    def registroEvento(self, test=None):
        if self.sd_factura_online_id.verificar_grupo_admin():
            self.validar_campos_necesarios()
            fact_online = self.sd_factura_online_id
            cfg = fact_online.getConfig(fact_online.sd_codigo_modalidad, fact_online.sd_codigo_ambiente,
                                        fact_online.sd_codigo_sistema,
                                        fact_online.sd_nombre_sistema, fact_online.sd_nit_em,
                                        fact_online.sd_nombre_company, fact_online.sd_tipo_sistema, fact_online.sd_token)

            service = ServiceOperaciones()
            service.setConfig(cfg)
            service.cuis = fact_online.sd_cuis
            service.cufd = fact_online.sd_cufd
            # service.codigoControl = resCufd['codigoControl']
            punto_venta = fact_online.sd_codigo_punto_venta.sd_codigo_punto_venta if fact_online.sd_es_punto_venta else 0

            sd_res = False
            res = service.registroEventoSignificativo(
                int(self.sd_evento_id.sd_codigo_clasificador),
                self.sd_evento_id.sd_descripcion,
                self.sd_cufd_antiguo,
                fact_online.obtener_fecha_backend(self.sd_fecha_inicio),
                fact_online.obtener_fecha_backend(self.sd_fecha_fin),
                int(fact_online.sd_codigo_sucursal),
                punto_venta
            )
            if res:
                print(res)
                if res['transaccion'] == True:
                    self.write({
                        'sd_codigo_recepcion_evento_significativo': res['codigoRecepcionEventoSignificativo'],
                        'state': 'register'
                    })
                    self.sd_cufd_id.write({
                        'sd_is_register': True
                    })
                    if not test:
                        mjs = self.sd_factura_online_id.mensaje_personalizador('Se registro con éxito el evento significativo')
                        return mjs
                else:
                    mensaje = res['mensajesList'][0]['descripcion']
                    raise UserError(_('"%s"\n Por favor verifique sus parametros') % (mensaje))
            else:
                raise UserError(_('Hubo un error inesperado. Por favor comuniquese con su soporte \n - Fallos de internet \n -fallos de servidores siat'))

    def obtenerFecha(self, fecha):
        fecha = fecha[:-8]
        fecha = fecha.replace(' ', 'T')
        return fecha

    def validar_campos_necesarios(self):
        if not self.sd_cufd_id:
            raise UserError(_('Es necesario el campo Cufd para continuar'))
        if not self.name:
            raise UserError(_('Es necesario el campo Nombre para continuar'))
        if not self.sd_factura_online_id:
            raise UserError(_('Es necesario el campo Factura en Linea para continuar'))
        if not self.sd_cuis:
            raise UserError(_('Es necesario el campo Cuis para continuar'))
        if not self.sd_cufd_antiguo:
            raise UserError(_('Es necesario el campo Cufd Antiguo para continuar'))
        if not self.sd_fecha_inicio:
            raise UserError(_('Es necesario el campo Fecha de Inicio para continuar'))
        if not self.sd_fecha_fin:
            raise UserError(_('Es necesario el campo Fecha Fin para continuar'))
        if not self.sd_evento_id:
            raise UserError(_('Es necesario el campo Contigencia para continuar'))

