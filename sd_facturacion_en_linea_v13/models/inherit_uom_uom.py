from odoo import api, fields, models, _

class InheritUomUom(models.Model):
    _inherit = 'uom.uom'

    sd_unidad_medida_id = fields.Many2one('unidad.medida.siat', string='Unidad Medida Siat')