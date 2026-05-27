from odoo import api, fields, models, tools


class InheritStockPicking(models.Model):
    _inherit = 'stock.picking'
    sd_es_devolucion = fields.Boolean(string="Es Devolución")

    @api.onchange('location_id')
    def not_change_location_id(self):
        print('reemplace la funcion para poder modificar la ubicacion origen')

    @api.onchange('location_dest_id')
    def not_change_location_dest_id(self):
        print('reeemplace la funcion para poder modificar la ubicacion destino')
