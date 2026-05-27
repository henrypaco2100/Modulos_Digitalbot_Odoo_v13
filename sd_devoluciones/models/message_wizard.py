from odoo import api, fields, models, _

class SDReturnsMessageWizard(models.TransientModel):
    _name = 'returns.message.wizard'
    _description = "Show Message"

    message = fields.Text('Message', required=True)

    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}