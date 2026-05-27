from odoo import api, fields, models,SUPERUSER_ID,_


class InheritStockMoveLineMejoraPlural(models.Model):
    _inherit = "stock.move.line"

    sd_pvp_product = fields.Float('Precio Venta', compute='compute_pvp_product', store=False)

    @api.depends('product_id')
    def compute_pvp_product(self):
        for stock_move_line in self:
            stock_move_line.update({
                'sd_pvp_product': stock_move_line.product_id.lst_price
            })
