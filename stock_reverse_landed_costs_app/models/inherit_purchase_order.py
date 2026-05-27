from odoo import models, api,fields

class SdInheritPurchaseOrderCancelarCostoDestino(models.Model):
    _inherit = 'purchase.order'
    def button_cancel(self):
        """Heredar funcion cancelar para cancelar los coste en destino de la compra"""
        if self.landed_costs_ids_purchase:
            for landed_costs_id in self.landed_costs_ids_purchase:
                landed_costs_id.button_cancel()

        res= super(SdInheritPurchaseOrderCancelarCostoDestino, self).button_cancel()
        return res