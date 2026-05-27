from odoo import api, fields, models, _

class MetodoPagoSiat(models.Model):
    _name = 'metodo.pago.siat'

    name = fields.Char(related="sd_descripcion")
    sd_codigo_clasificador = fields.Integer(string="Código Clasificador")
    sd_descripcion = fields.Char(string="Descripción", readonly=True)
    sd_activo = fields.Boolean(string='Activo')
    company_id = fields.Many2one('res.company', string='Compañía')

    # @api.model
    # def create(self, vals):
    #     if not vals.get('company_id'):
    #         vals['company_id'] = self.env.user.company_id.id
    #     return super(MetodoPagoSiat, self).create(vals)