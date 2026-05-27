from odoo import api, fields, models, _

class InheritProductCategory(models.Model):
    _inherit = 'product.category'

    sd_codigo_product_id = fields.Many2one('product.service.siat', 'Producto Sin')
    # sd_unidad_medida_id = fields.Many2one('unidad.medida.siat', string='Unidad Medida Siat')