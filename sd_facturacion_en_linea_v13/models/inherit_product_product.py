from odoo import api, fields, models, _

class InheritProductTemplate(models.Model):
    _inherit = 'product.template'

    sd_codigo_product_id = fields.Many2one(related='categ_id.sd_codigo_product_id')
    sd_factura_online_id = fields.Many2one('online.billing.siat', string='Factura en linea')
    sd_unidad_medida_id = fields.Many2one('unidad.medida.siat', string='Unidad Medida Siat', related='uom_id.sd_unidad_medida_id')
    # sd_homologacion_code =
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, index=1)
class InheritProductProduct(models.Model):
    _inherit = 'product.product'

    sd_codigo_product_id = fields.Many2one('product.service.siat', 'Producto Sin', related='product_tmpl_id.sd_codigo_product_id')
    sd_unidad_medida_id = fields.Many2one('unidad.medida.siat', 'Unidad Media Siat', related='uom_id.sd_unidad_medida_id')
