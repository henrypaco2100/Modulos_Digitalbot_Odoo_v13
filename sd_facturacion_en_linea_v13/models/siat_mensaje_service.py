from odoo import api, fields, models, _

class MensajeServiceSiat(models.Model):
    _name = 'mensaje.service.siat'

    name = fields.Char(related="sd_descripcion")
    sd_codigo_clasificador = fields.Char(string="Código Clasificador", readonly=1)
    sd_descripcion = fields.Char(string="Descripción", readonly=1)