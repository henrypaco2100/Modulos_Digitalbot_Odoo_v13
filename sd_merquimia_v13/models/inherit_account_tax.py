from odoo import api, fields, models, _, tools

class SdInheritSaleOrdenMejorasMerquimia(models.Model):
    _inherit = 'account.tax'
    sd_show = fields.Boolean(string="Mostrar")


