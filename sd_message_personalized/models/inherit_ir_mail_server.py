from odoo import api, fields, models, _

class SdInheritIrMailServer(models.Model):
    _inherit = 'ir.mail_server'
    _description = "Herencia al servidor de correo"

    res_partner = fields.Many2one('res.partner',string="Contacto Adminstrador")