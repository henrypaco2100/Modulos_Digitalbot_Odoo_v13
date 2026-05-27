from odoo import api, fields, models, _

class PuntoVentaSiat(models.Model):
    _name = 'punto.venta.siat'

    name = fields.Char(related='sd_descripcion', string='Nombre')

    sd_codigo_clasificador = fields.Integer(string='Código Clasificador')
    sd_descripcion = fields.Char(string='Descripcion')