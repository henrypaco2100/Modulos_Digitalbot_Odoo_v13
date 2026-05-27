from odoo import models, api, _, fields
from odoo.exceptions import UserError

class ModoOfflineWizard(models.TransientModel):
    _name = "wizard.modo.offline"
    _description = "Cambiar fuera de linea"

    @api.model
    def default_get(self, fields):
        res = super(ModoOfflineWizard, self).default_get(fields)

        invoice_id = self.env.context.get('default_id') or self.env.context.get('active_id')
        if invoice_id:
            invoice = self.env['account.move'].browse(invoice_id)
        if invoice.exists():
            invoice.ensure_one()
            if 'invoice_id' in fields:
                res['invoice_id'] = invoice.id

        return res

    invoice_id = fields.Many2one('account.move', 'Factura')

    def cambiar_modo_offline(self):
        if self.invoice_id:
            self.invoice_id.cambiar_endpoint()