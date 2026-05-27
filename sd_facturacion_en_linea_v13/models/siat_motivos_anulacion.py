from odoo import api, fields, models, _

class SiatMotivoAnulacion(models.Model):
    _name = 'motivo.anulacion.siat'
    _res_name = 'sd_descripcion'

    name = fields.Char(related='sd_descripcion')
    sd_codigo_clasificador = fields.Integer('Código Clasificador')
    sd_descripcion = fields.Char(string='Descripción')
