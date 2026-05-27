from odoo import api, fields, models, _

class SucursalFacturaSiat(models.Model):
    _name = 'sucursal.factura.siat'

    name = fields.Char(string="Nombre")
    sd_codigo_clasificador = fields.Integer(string="Código Clasificador")
    sd_descripcion = fields.Char(related="name")
    # sd_activo = fields.Boolean(string='Activo')
    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)