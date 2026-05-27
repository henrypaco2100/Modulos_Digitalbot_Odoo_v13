from odoo import api, fields, models, _

class documentoIdentidadSiat(models.Model):
    _name = 'documento.identidad.siat'

    name = fields.Char(related="sd_descripcion")
    sd_codigo_clasificador = fields.Integer(string="Código Clasificador", readonly=True)
    sd_descripcion = fields.Char(string="Descripción", readonly=True)