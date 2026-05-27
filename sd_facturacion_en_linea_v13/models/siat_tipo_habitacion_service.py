from odoo import api, fields, models, _

class tipoHabitacionSiat(models.Model):
    _name = 'tipo.habitacion.siat'

    name = fields.Char(related="sd_descripcion")
    sd_codigo_clasificador = fields.Integer(string="Código Clasificador")
    sd_descripcion = fields.Char(string="Descripción")