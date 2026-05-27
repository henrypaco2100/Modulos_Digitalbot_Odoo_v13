from odoo import api, fields, models, _

class leyendaFacturaSiat(models.Model):
    _name = 'leyenda.factura.siat'

    name = fields.Char(related="sd_descripcion_leyenda")
    sd_codigo_actividad_id = fields.Many2one('factura.actividades', string='Tipo Actividad')
    sd_descripcion_leyenda = fields.Char('Descripción leyenda')
    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)