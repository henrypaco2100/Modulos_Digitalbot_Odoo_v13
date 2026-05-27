from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from datetime import datetime, timedelta
import time

class SdInheritOnlineBillingSiat(models.Model):
    _inherit = 'online.billing.siat'

    def cron_consultar_estado_conexion(self):
        factura_online_ids = self.env['online.billing.siat'].search([('sd_tipo_emision', '=', '2')])
        if factura_online_ids:
            for factura_online_id in factura_online_ids:
                res_comunicacion = factura_online_id.verificar_comunicacion_siat()
                if res_comunicacion:
                    factura_online_id.write({
                        'sd_contador_conexion': factura_online_id.sd_contador_conexion + 1
                    })
                else:
                    factura_online_id.write({
                        'sd_contador_conexion': 0
                    })
                if factura_online_id.sd_contador_conexion == 1:
                    factura_online_id.write({'sd_tipo_emision': '1'})
                    factura_online_id.write({
                        'sd_contador_conexion': 0
                    })
                    factura_online_id.sd_evento_id.write({
                        'sd_fecha_fin': datetime.now()
                        #posiblemente se deba aumentar 4 horas como hace odoo
                    })

                    factura_online_id.solicitudCufd(test=True)
                    factura_online_id.sd_evento_id.registroEvento()
                    self.recopilar_facturas_evento(factura_online_id.sd_evento_id, factura_online_id)
        # else:
            # time.sleep(10)
            # self.sudo().apagar_bot()

    def recopilar_facturas_evento(self, evento, fact_online):
        fecha_inicio = evento.sd_fecha_inicio
        fecha_fin = evento.sd_fecha_fin
        facturas = self.env['account.move'].search([('sd_is_offline','=',True), ('sd_es_cafc','=',False)]).filtered(lambda s: s.sd_fecha_emision > fecha_inicio and s.sd_fecha_emision < fecha_fin or
                      s.sd_fecha_emision == fecha_inicio or s.sd_fecha_emision == fecha_fin)
        # print(factura.sd_fecha_emision for factura in facturas)
        data = {
            'name': 'paquete ' + evento.name + ' ' + str(evento.sd_fecha_inicio),
            'sd_factura_online_id': fact_online.id,
            'sd_evento_id': evento.id,
            'sd_fecha_inicio': fecha_inicio,
            'sd_codigo_sucursal': fact_online.sd_codigo_sucursal,
            'sd_tipo_factura': fact_online.sd_tipo_factura,
            'sd_codigo_documento_sector': fact_online.sd_codigo_documento_sector,
            'sd_invoice_ids': [factura.id for factura in facturas],
            'sd_cafc': None,
        }
        recepcion_paquete = self.env['siat.emision.paquete.offline'].create(data)
        recepcion_paquete.registroEmisionPaquetes(esBot='es_bot')
        recepcion_paquete.validacionRecepcionPaquete(esBot='es_bot')

    def encender_bot(self):
        cron_id = self.env['ir.model.data'].xmlid_to_res_id('sd_facturacion_en_linea_v13.sd_evento_significativo_cron')
        automated = self.env['ir.cron'].sudo().search([('id', '=', cron_id), ('active', '=', False)])
        if automated:
            self.encender_apagar_bot(automated)

    def apagar_bot(self):
        cron_id = self.env['ir.model.data'].xmlid_to_res_id('sd_facturacion_en_linea_v13.sd_evento_significativo_cron')
        automated = self.env['ir.cron'].sudo().search([('id', '=', cron_id), ('active', '=', True)])
        if automated:
            self.encender_apagar_bot(automated)

    def encender_apagar_bot(self, automated):
        cambio_estado = not automated.active
        automated.sudo().write({
            'active': cambio_estado
        })