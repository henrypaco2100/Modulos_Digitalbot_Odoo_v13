from odoo import api, fields, models,SUPERUSER_ID,_

class InheritProductTemplateMejora(models.Model):
    _inherit = 'product.template'

    type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service'),
        ('product', 'Almacenable')], string='Product Type', default='product', required=True,
        help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A consumable product is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.')
    sd_codigo_interno = fields.Char('Codigo Interno')

    # @api.onchange('type')
    # def _onchange_type(self):
    #     # Do nothing but needed for inheritance
    #     return {}
