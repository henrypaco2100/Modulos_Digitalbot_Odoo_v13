
from odoo import api, fields, models, _, tools

class posSessionInherit(models.Model):
    _inherit = "pos.session"

    def _compute_picking_count(self):
        vals = super(posSessionInherit, self)._compute_picking_count()
        for pos in self:
            pickings = pos.order_ids.mapped('picking_id').filtered(lambda x: x.state not in ('done', 'cancel'))
            pos.picking_count = len(pickings.ids)
        return vals

    def action_stock_picking(self):
        vals = super(posSessionInherit, self).action_stock_picking()
        pickings = self.order_ids.mapped('picking_id').filtered(lambda x: x.state not in ('done', 'cancel'))
        action_picking = self.env.ref('stock.action_picking_tree_ready')
        action = action_picking.read()[0]
        action['context'] = {}
        action['domain'] = [('id', 'in', pickings.ids)]
        return vals
