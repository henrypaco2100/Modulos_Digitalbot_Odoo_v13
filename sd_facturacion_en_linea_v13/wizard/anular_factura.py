from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

class SdFacturaEnLineaAnular(models.TransientModel):
    _name = 'online.billing.wizard.anular'

    sd_motivo_online = fields.Many2one('motivo.anulacion.siat', string='Motivo de Anulación')

    @api.model
    def default_get(self, fields):
        res = super(SdFacturaEnLineaAnular, self).default_get(fields)

        invoice_id = self.env.context.get('default_id') or self.env.context.get('active_id')
        if invoice_id:
            invoice = self.env['account.move'].browse(invoice_id)
        if invoice.exists():
            invoice.ensure_one()
            if 'invoice_id' in fields:
                res['invoice_id'] = invoice.id

        return res

    invoice_id = fields.Many2one('account.move', 'Factura')

    def action_anular_factura_online(self):
        if self.invoice_id:
            self.invoice_id.write({
                'sd_motivo_id': self.sd_motivo_online.id
            })
            self.invoice_id.button_cancel()