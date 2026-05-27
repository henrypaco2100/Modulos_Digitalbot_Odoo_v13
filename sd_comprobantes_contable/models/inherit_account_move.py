from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SdInheritAccountMoveMejoras(models.Model):
    _inherit = "account.move"

    sd_is_fecha = fields.Boolean('Columna Fecha')

