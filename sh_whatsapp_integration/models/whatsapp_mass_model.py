from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ast import literal_eval

class WhatsappMass(models.Model):
    _name = "whatsapp.mass"

    _description = "Listado de mensajes masivos de whatsapp"

    sd_mensaje = fields.Text(string="Mensaje", required=True)
    sd_descriptivo = fields.Text(string="Descripción")
    sd_sale_name = fields.Char(string="Venta")
    sd_purchase_name = fields.Char(string="Compra")

    sd_fecha_inicial = fields.Date(string="Fecha inicial", default=fields.Datetime.now)
    sd_fecha_envio = fields.Date(string="Fecha de envio")
    sd_url = fields.Char(string="Link")

    sd_documento = fields.Binary(string="Documento Adjunto")
    contacto_domain = fields.Char(string="domain", default=[])
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_queue', 'En Cola'),
        ('send', 'Enviado')
    ], tracking=True, readonly=True, default='draft')

    def send_whatsapp_direct(self):
            sd_domain = literal_eval(self.contacto_domain) if self.contacto_domain else []
            contacto_ids = self.env['res.partner'].search(sd_domain)
            if contacto_ids:
                for contacto_id in contacto_ids:
                    if not contacto_id.mobile:
                        raise UserError(_("El contacto %s no tiene número de celular") % contacto_id.name)
                    else:

                        cola = {
                            'sd_contacto_id': contacto_id.id,
                            'sd_fecha_inicial': fields.Datetime.now(),
                            'sd_whatsapp_mass_id': self.id
                        }
                        self.env['list.contact.message'].create(cola)

                        self.write({
                            'state': 'in_queue'
                        })
            else:
                raise UserError("No existe ningun contacto")

    def change_state(self):
        self.write({
            'state': 'draft'
        })

    def action_list_message_tree(self):
        action = self.env.ref('sh_whatsapp_integration.action_arbol_list_contact_message').read()[0]

        action['domain'] = [('sd_whatsapp_mass_id', '=', self.id)]
        return action
