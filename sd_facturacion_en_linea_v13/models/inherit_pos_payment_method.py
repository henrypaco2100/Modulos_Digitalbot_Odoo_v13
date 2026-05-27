from odoo import api, fields, models, _
from odoo.exceptions import UserError

class InheritPosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    sd_metodo_pago_siat = fields.Many2one('metodo.pago.siat', string="Metodo Pago", domain=[('sd_activo', '=', True)])
    sd_es_tarjeta = fields.Boolean('Es tarjeta', default=False)