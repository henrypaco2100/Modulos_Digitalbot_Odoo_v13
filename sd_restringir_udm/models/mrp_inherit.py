from odoo import models, fields, api, _

class InheritProductoTemplateUDMMrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_uom_sub_category_id = fields.Many2one(related='product_id.uom_id.sd_sub_categoria',readonly=True)
    # product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        readonly=True, required=True,
        states={'draft': [('readonly', False)]},
        domain="[('sd_sub_categoria', '=', product_uom_sub_category_id)]")