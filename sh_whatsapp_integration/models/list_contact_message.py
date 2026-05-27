from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ListContactMessage(models.Model):
    _name = "list.contact.message"
    _description = '''
    Este modulo es un detalle de todoos los contactos que resiviran mensajes
    '''
    sd_contacto_id = fields.Many2one('res.partner', string="Contacto")
    sd_contacto_number = fields.Char(string="Celular", related='sd_contacto_id.mobile')
    sd_fecha_inicial = fields.Date(string="Fecha inicial", default=fields.Datetime.now)
    sd_fecha_envio = fields.Date(string="Fecha de envio")
    sd_url = fields.Char(string="Link")
    sd_contacto_image = fields.Binary(string="Foto", related="sd_contacto_id.image_1920")
    sd_whatsapp_mass_id = fields.Many2one('whatsapp.mass', string='whatsapp masivo')
    sd_descripcion = fields.Text(string="Descripción", related="sd_whatsapp_mass_id.sd_descriptivo")
    sd_mensaje_1 = fields.Text(string="Mensaje", related="sd_whatsapp_mass_id.sd_mensaje")
    state = fields.Selection([
        ('in_queue', 'En Cola'),
        ('send', 'Enviado')],
        default='in_queue', string='Estado')
    # def create(self):
    #     res =super(ListContactMessage, self).create()
    #     print('hola')
    #     return res

    def action_enviar_message(self):
        if self.sd_contacto_number:

            self.write({
                'sd_url': "https://web.whatsapp.com/send?l=&phone=" + self.sd_contacto_number + "&text=" + self.sd_mensaje_1,
                'state': "send"
            })

            messages_verify = self.env['list.contact.message'].search([('sd_whatsapp_mass_id','=', self.sd_whatsapp_mass_id.id)])
            send_all = True
            if messages_verify:
                for message in messages_verify:
                    if message.state != 'send':
                        send_all = False

            if send_all:
                whatsapp_mass = self.env['whatsapp.mass'].search([('id','=',self.sd_whatsapp_mass_id.id)])
                whatsapp_mass.write({
                    'state': 'send',
                    'sd_fecha_envio': fields.Datetime.now()
                })

            return {
                'type': 'ir.actions.act_url',
                'url': "https://web.whatsapp.com/send?l=&phone=" + self.sd_contacto_number + "&text=" + self.sd_mensaje_1,
                'target': 'new',
                'res_id': self.sd_whatsapp_mass_id,
            }
        else:
            raise UserError("El número de móvil del contacto no existe")