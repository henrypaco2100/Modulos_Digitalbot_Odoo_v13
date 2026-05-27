from odoo import api, fields, models, _, tools

class SdInheritSaleOrdenMejorasMerquimia(models.Model):
    _inherit = 'res.users'
    sd_comercial= fields.Boolean(string="Comercial")



