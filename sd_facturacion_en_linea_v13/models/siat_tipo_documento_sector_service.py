from odoo import api, fields, models, _

class tipoDocumentoSectorSiat(models.Model):
    _name = 'tipo.documento.sector.siat'

    name = fields.Char(related="sd_descripcion")
    sd_codigo_clasificador = fields.Integer(string="Código Clasificador")
    sd_descripcion = fields.Char(string="Descripción")
    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)