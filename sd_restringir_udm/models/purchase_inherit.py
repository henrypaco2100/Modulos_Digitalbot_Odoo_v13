from odoo import models, fields, api, _

class InheritProductoTemplateUDMOPurchaseorderLine(models.Model):
    _inherit = 'purchase.order.line'
    # @api.depends('product_id')
    # def _compute_restringir_udm_purchase(self):
    #     print("producto ",self.product_id)
    #     if self.product_id:
    #         producto_template = self.env['product.template'].search([('id','=',self.product_id.id)])
    #         if producto_template.sd_udm_restringir_compra:
    #             udm = producto_template.sd_udm_restringir_compra
    #         else:
    #             udm = self.env['uom.uom'].search([('category_id', '=', producto_template.uom_po_id.category_id.id)])
    #         print(udm)
    #         return udm.mapped('id')

    # product_uom_retringir = fields.Many2many(related='product_id.sd_udm_restringir_compra')
    # product_uom = fields.Many2one('uom.uom', string='Unit of Measure',domain=lambda self: [('id', 'in', self._compute_restringir_udm_purchase())])
    # prueba_campo = fields.Char(string='hello')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.sd_sub_categoria')
    # categoria_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('sd_sub_categoria', '=', product_uom_category_id)]")
