from odoo import models, fields, api, _

class InheritUDM_Restringir(models.Model):
    _inherit = 'uom.uom'

    sd_sub_categoria = fields.Many2one('sub.category.udm','SubCategoria')
