from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class SdInheritAccountCompraIvaPlural(models.Model):
    _inherit = 'account.move'

    sd_credito_fiscal = fields.Boolean('Credito fiscal', default=False)
    sd_compra_iva_ids = fields.One2many('compra.iva', 'sd_move_id', string='Compras')