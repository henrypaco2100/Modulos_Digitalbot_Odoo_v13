from odoo import api, fields, models, _

class tipoActividadDocumentoSiat(models.Model):
    _name = 'tipo.actividad.documento.siat'

    name = fields.Char(related="sd_tipo_doc_sector")
    sd_codigo_actividad_id = fields.Many2one('factura.actividades', string='Tipo Actividad')
    sd_codigo_doc_sector_id = fields.Many2one('tipo.documento.sector.siat', string='Tipo Documento Sector')
    sd_tipo_doc_sector = fields.Char('Tipo de Documento Sector')