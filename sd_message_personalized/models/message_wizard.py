from odoo import api, fields, models, _

class SdMessageWizard(models.TransientModel):
    _name = 'sd.message.wizard'
    _description = "show mensaje"

    message = fields.Text('Message', required=True)

    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}

    """
    Usar el siguiente COdigo para retornar un mensaje
    
    mensaje = " se realizo con exito!!!"
    message_id = self.env['sd.message.wizard'].create({'message': mensaje  })
    return {
        'name': 'Proceso Exitoso!!',
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'res_model': 'sd.message.wizard',
        'res_id': message_id.id,
        'target': 'new'
    }
    
    """