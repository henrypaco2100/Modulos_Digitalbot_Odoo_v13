from odoo import models, api, _, fields
from odoo.exceptions import UserError
from datetime import datetime, timedelta
class PaqueteFacturaWizard(models.TransientModel):
    _name = "wizard.paquete.factura"
    _description = "Creacion Paquete Factura"

    sd_online_billing_id = fields.Many2one('online.billing.siat', 'Facturacion siat')
    @api.model
    def default_get(self, fields):
        res = super(PaqueteFacturaWizard, self).default_get(fields)

        sd_online_billing_id = self.env.context.get('default_id') or self.env.context.get('active_id')
        if sd_online_billing_id:
            online_billing = self.env['online.billing.siat'].browse(sd_online_billing_id)
        if online_billing.exists():
            online_billing.ensure_one()
            if 'sd_online_billing_id' in fields:
                res['sd_online_billing_id'] = online_billing.id

        return res


    # sd_evento_id = fields.Many2one('eventos.significativos.siat', 'Evento Significativo')
    sd_facturas_ids = fields.One2many('wizard.auxiliar.paquete', 'paquete_wizard_id')
    sd_name = fields.Char('Nombre')

    # def action_publicar_facturas_paquetes(self):
    #     if self.sd_online_billing_id:
    #         fact_online = self.sd_online_billing_id
    #         self.cargar_facturas_paquetes(fact_online.sd_evento_significativo_id)
    #         vals = {
    #             'sd_factura_online_id': fact_online.id,
    #             'sd_evento_id': fact_online.sd_evento_significativo_id.id,
    #             'name': self.sd_name,
    #             'sd_invoice_ids': self.sd_facturas_ids
    #         }
    #         paquete = self.env['siat.emision.paquete.offline'].create(vals)
    #         paquete.registroEmisionPaquetes()
    #         paquete.validacionRecepcionPaquete()
    #
    # def cargar_facturas_paquetes(self, sd_evento_id):
    #     if sd_evento_id.sd_fecha_inicio and sd_evento_id.sd_fecha_fin:
    #         fecha_inicio = sd_evento_id.sd_fecha_inicio
    #         fecha_fin = sd_evento_id.sd_fecha_fin
    #         facturas = self.env['account.move'].search([('sd_es_cafc','=',True)]).filtered(lambda s: s.sd_fecha_emision > fecha_inicio and s.sd_fecha_emision < fecha_fin or
    #                       s.sd_fecha_emision == fecha_inicio or s.sd_fecha_emision == fecha_fin)
    #         self.update({
    #             'sd_facturas_ids': [factura.id for factura in facturas]
    #         })
    #     else:
    #         raise UserError(_('Por favor ingrese las fechas de inicio y fin para obtener las facturas correspondientes'))

class PaqueteAuxiliarWizard(models.TransientModel):
    _name = "wizard.auxiliar.paquete"
    _description = "Creacion Paquete Factura"

    # @api.model
    # def default_get(self, fields):
    #     res = super(PaqueteAuxiliarWizard, self).default_get(fields)
    #
    #     sd_online_billing_id = self.env.context.get('default_id') or self.env.context.get('active_id')
    #     if sd_online_billing_id:
    #         online_billing = self.env['wizard.paquete.factura'].browse(sd_online_billing_id)
    #         if online_billing.exists():
    #             online_billing.ensure_one()
    #             if 'paquete_wizard_id' in fields:
    #                 res['paquete_wizard_id'] = online_billing.id
        # return res
    paquete_wizard_id = fields.Many2one('wizard.paquete.factura')
    sd_invoice_id = fields.Many2one('account.move','factura')

