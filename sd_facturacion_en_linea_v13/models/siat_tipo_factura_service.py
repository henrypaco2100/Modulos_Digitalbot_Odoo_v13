from odoo import api, fields, models, _

class tipoFacturaSiat(models.Model):
    _name = 'tipo.factura.siat'

    name = fields.Char(related="sd_descripcion")
    sd_codigo_clasificador = fields.Integer(string="Código Clasificador")
    sd_descripcion = fields.Char(string="Descripción")