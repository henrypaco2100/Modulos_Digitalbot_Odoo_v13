from odoo import api, fields, models,SUPERUSER_ID,_
from odoo.exceptions import UserError, ValidationError
class InheritStockPickingRestric(models.Model):
    _inherit = "stock.picking"

    def action_confirm(self):
        if self.picking_type_id.code in ['internal','outgoing']:
            for stock_move in self.move_ids_without_package:
                if not stock_move.product_uom_qty <= stock_move.sd_stock_disponible and stock_move.product_id.custom_check_onhand_qty:
                    raise UserError(_('Stock Disponible insuficiente!!\nLa demanda no puede ser mayor al stock disponible\nNo es posible continuar.'))
        res = super(InheritStockPickingRestric, self).action_confirm()
        return res