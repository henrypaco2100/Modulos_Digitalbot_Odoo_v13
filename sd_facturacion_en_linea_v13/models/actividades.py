from odoo import _, models, api, fields

class Actividades(models.Model):
    _name = 'factura.actividades'

    name = fields.Char(string='Nombre',related="sd_descripcion", readonly=True)
    sd_codigo_caeb = fields.Char(string="Codigo Caeb", readonly=True)
    sd_descripcion = fields.Char(string="descripcion", readonly=True)
    sd_tipo_actividad = fields.Char(string="Tipo actividad", readonly=True)
