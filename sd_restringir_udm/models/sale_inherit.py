from odoo import models, fields, api, _

class InheritProductoTemplateUDMOsaleorderLine(models.Model):
    _inherit = 'sale.order.line'

    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('sd_sub_categoria', '=', product_uom_category_id)]")
    # product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.sd_sub_categoria', readonly=True)