from odoo import api, fields, models, _

class MensajeEventoSiat(models.Model):
    _name = 'mensaje.eventos.siat'

    name = fields.Char(related='sd_descripcion', string='Nombre')
    sd_codigo_clasificador = fields.Integer(string='Código Clasificador', readonly=True)
    sd_descripcion = fields.Char(string='Descripción', readonly=True)