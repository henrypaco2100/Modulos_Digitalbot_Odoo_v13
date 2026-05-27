from odoo import models, fields, api, _
# Modelo para actualizar el precio del producto al realizar una nueva Compra
class InheritPurchaseUpdateProduct(models.Model):
    _inherit='purchase.order'
    _campo_prueba= fields.Char(string='prueba')
    @api.depends('state')
    def _actualizar_precio_product(self):
        print("se actualiza")