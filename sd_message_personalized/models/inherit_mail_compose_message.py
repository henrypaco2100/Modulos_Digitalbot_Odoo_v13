from odoo import api, fields, models, _

class SdInheritMailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'
    _description = "Herencia al mail compose message"

    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        vals = super(SdInheritMailComposeMessage, self).onchange_template_id( template_id, composition_mode, model, res_id)
        print('self', self.model)
        print('vals super 1', vals)
        if self.model in ['sale.order','purchase.order']:
            print('si entra',self.env.user.email_formatted)
            if 'value' in vals:
                if 'email_from' in vals['value']:
                    print('entra email_from')
                    vals['value']['email_from'] = self.env.user.email_formatted

        print('vals super 2',vals)
        return vals