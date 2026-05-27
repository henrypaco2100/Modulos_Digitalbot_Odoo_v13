from odoo import models, api, _, fields
from odoo.exceptions import UserError
from datetime import datetime, timedelta
class EventoSignificativoWizard(models.TransientModel):
    _name = "wizard.evento.significativo"
    _description = "Creacion Evento Significativo"

    @api.model
    def default_get(self, fields):
        res = super(EventoSignificativoWizard, self).default_get(fields)

        sd_online_billing_id = self.env.context.get('default_id') or self.env.context.get('active_id')
        if sd_online_billing_id:
            online_billing = self.env['online.billing.siat'].browse(sd_online_billing_id)
        if online_billing.exists():
            online_billing.ensure_one()
            if 'sd_online_billing_id' in fields:
                res['sd_online_billing_id'] = online_billing.id

        return res

    sd_online_billing_id = fields.Many2one('online.billing.siat', 'Facturacion siat')
    sd_name = fields.Char('Nombre')
    sd_fecha_inicio = fields.Datetime('Fecha Inicio')
    sd_fecha_fin = fields.Datetime('Fecha Fin')
    sd_cufd = fields.Many2one('factura.cufd', 'CUFD', domain=['sd_is_register','=',True])
    sd_cuis = fields.Char('CUIS', related='sd_online_billing_id.sd_cuis')
    sd_evento_id = fields.Many2one('mensaje.eventos.siat', 'Contingencia')
    sd_cufd_antiguo = fields.Char('Cufd Antiguo', related='sd_cufd.sd_cufd')

    def action_crear_evento_significativo(self):
        if self.sd_online_billing_id:
            self.sd_online_billing_id.sd_evento_significativo_id.write({
                'name': self.sd_name,
                'sd_factura_online_id': self.sd_online_billing_id.id,
                'sd_evento_id': self.sd_evento_id.id,
                'sd_cufd_id': self.sd_cufd.id,
                'sd_fecha_fin': datetime.now()
            })
            self.sd_online_billing_id.sd_evento_significativo_id.registroEvento()
            print('evento', self.sd_online_billing_id.sd_evento_significativo_id)





