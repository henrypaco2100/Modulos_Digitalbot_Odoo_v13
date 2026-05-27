from odoo import models, fields, api, _

class InheritProductoTemplateUDMOaccountorderLine(models.Model):
    _inherit = 'account.move.line'

    # product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure',
    #                               domain="[('sd_sub_categoria', '=', product_uom_sub_category_id)]")
    # # product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    # product_uom_sub_category_id = fields.Many2one(related='product_id.uom_id.sd_sub_categoria', readonly=True)