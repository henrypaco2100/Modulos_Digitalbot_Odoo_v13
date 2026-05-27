from odoo import api, fields, models, _

class SiatProductService(models.Model):
    _name = 'product.service.siat'
    _res_name = 'name'

    name = fields.Char(related='sd_descripcion_producto')
    sd_codigo_actividad = fields.Many2one('factura.actividades', string='Codigo Actividad')
    sd_codigo_producto = fields.Char(string='Codigo Producto')
    sd_descripcion_producto = fields.Char(string='Descripcion')
    sd_nandina_ids = fields.One2many('nandina.service.siat', 'sd_product_id', string='Nandina')
    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)


class SiatNandinaService(models.Model):
    _name = 'nandina.service.siat'
    sd_product_id = fields.Many2one('product.service.siat', string='Producto')
    sd_codigo_nandina = fields.Char(string='Nandina')