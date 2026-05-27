from odoo import models, fields, api, _

class InheritProductoTemplateUDMStockMove(models.Model):
    _inherit = 'stock.move'

    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', required=True,
                                  domain="[('sd_sub_categoria', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.sd_sub_categoria')


