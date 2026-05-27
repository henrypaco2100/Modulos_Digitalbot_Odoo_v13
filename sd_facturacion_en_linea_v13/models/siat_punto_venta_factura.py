from odoo import api, fields, models, _
from pysiat.services.service_operaciones import ServiceOperaciones
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class PuntoVentaFactura(models.Model):
    _name = 'punto.venta.factura'
    _rec_name = 'name'

    name = fields.Char('Nombre')
    sd_codigo_tipo_punto_venta_id = fields.Many2one('punto.venta.siat', string='Tipo Punto Venta')
    sd_descripcion = fields.Char('Descripción')
    sd_factura_online_id = fields.Many2one('online.billing.siat', string='Factura en Linea',
                                           domain="[('sd_es_punto_venta', '=', False)]")
    sd_cuis = fields.Char(related='sd_factura_online_id.sd_cuis')
    sd_res_punto_venta = fields.Char('respuesta')
    sd_codigo_punto_venta = fields.Integer('Codigo Punto Venta')
    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)

    def registrar_punto_venta(self):
        if self.sd_factura_online_id.verificar_grupo_admin():
            fact = self.sd_factura_online_id
            cfg = self.sd_factura_online_id.getConfig(fact.sd_codigo_modalidad, fact.sd_codigo_ambiente, fact.sd_codigo_sistema,
                                 fact.sd_nombre_sistema, fact.sd_nit_em,
                                 fact.sd_nombre_company, fact.sd_tipo_sistema, fact.sd_token)
            service = ServiceOperaciones()
            service.setConfig(cfg)
            service.cuis = self.sd_cuis
            res_punto_venta = service.registroPuntoVenta(int(fact.sd_codigo_sucursal),self.sd_codigo_tipo_punto_venta_id.sd_codigo_clasificador,self.name,self.sd_descripcion)
            if res_punto_venta:
                print(res_punto_venta)
                if res_punto_venta['transaccion']:
                    self.write({
                        'sd_codigo_punto_venta': res_punto_venta['codigoPuntoVenta']
                    })
                    mjs = fact.mensaje_personalizador('Punto de venta registrado con éxito.')
                    return mjs
                else:
                    mensaje_error = 'Fallo el registro por lo siguiente: \n'
                    for mensaje in res_punto_venta['mensajesList']:
                        mensaje_error = mensaje_error + mensaje['descripcion'] + '\n'
                    raise UserError(_(mensaje_error))
            else:
                raise UserError(_('Hubo un error inesperado, vuelva a intentar. \n Comuniquese con su soporte.'))
