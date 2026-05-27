from odoo import models, fields, api, _

class SdStockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    sd_reserve_qty = fields.Float(string='Reservado', default=0.0)

    def action_reservar_lot(self,cantidad_reservar):
        """
        Metodo de reserva de lotes.
        si la reserva supera al stock entonces se reserva lo disponible y retorna un
        """
        if 0 <= (self.product_qty - cantidad_reservar):
            self.sudo().write({
                'product_qty':self.product_qty - cantidad_reservar,
                'sd_reserve_qty':self.sd_reserve_qty + cantidad_reservar,
            })
        else:
            self.sudo().write({
                'product_qty': self.product_qty - self.product_qty,
                'sd_reserve_qty': self.product_qty,
            })
        print(self.product_qty)
        return self.sd_reserve_qty
    def do_unreserve_lot(self,qty_reserve):
        self.sudo().write({
            # 'product_qty': self.product_qty + qty_reserve,
            'sd_reserve_qty': 0#self.qty_reserve - qty_reserve,
        })