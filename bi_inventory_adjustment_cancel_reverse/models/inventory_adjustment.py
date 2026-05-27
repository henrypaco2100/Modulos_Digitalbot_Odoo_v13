# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import logging
from odoo.tools.float_utils import float_round, float_is_zero
_logger = logging.getLogger(__name__)


class Inventory(models.Model):
    _inherit = 'stock.inventory'

    def action_cancel_draft(self):
        self.mapped('move_ids')._action_cancel()
        self.write({'line_ids': [(5,)], 'state': 'cancel'})
        # if self.filter == 'lot':
        for move in self.move_ids:
            quants_dest_lot_id = self.env['stock.quant'].sudo().search([('product_id','=',move.product_id.id),('location_id','=',move.location_dest_id.id)])
            quants_src_lot_id = self.env['stock.quant'].sudo().search([('product_id','=',move.product_id.id),('location_id','=',move.location_id.id)])
            if quants_dest_lot_id:
                if quants_dest_lot_id[0].product_id.tracking == 'lot':
                    if quants_dest_lot_id[0].reserved_quantity:
                        old_qty = quants_dest_lot_id[0].quantity
                        quants_dest_lot_id[0].quantity = old_qty - move.product_uom_qty
                        quants_dest_lot_id[0].quantity = quants_dest_lot_id[0].quantity  - quants_dest_lot_id[0].reserved_quantity
                    else:
                        old_qty = quants_dest_lot_id[0].quantity
                        quants_dest_lot_id[0].quantity = old_qty - move.product_uom_qty
                else:
                    if quants_dest_lot_id[0].reserved_quantity:
                        old_qty = quants_dest_lot_id[0].quantity
                        quants_dest_lot_id[0].quantity = old_qty - move.product_uom_qty
                        quants_dest_lot_id[0].quantity = quants_dest_lot_id[0].quantity  - quants_dest_lot_id[0].reserved_quantity
                    else:
                        old_qty = quants_dest_lot_id[0].quantity
                        quants_dest_lot_id[0].quantity = old_qty - move.product_uom_qty
            if quants_src_lot_id:
                if quants_src_lot_id[0].product_id.tracking == 'lot':
                    old_qty = quants_src_lot_id[0].quantity
                    quants_src_lot_id[0].quantity = old_qty + move.product_uom_qty

            account_move = self.env['account.move'].sudo().search([('stock_move_id', '=', move.id)], order="id desc", limit=1)
            if account_move:
                account_move.button_cancel()

            # Cancelar valoracion -HENRY
            for stock_valuation_layer in move.stock_valuation_layer_ids:
                if stock_valuation_layer.state == 'confirmed':
                    if stock_valuation_layer.valuation_detailed:
                        stock_valuation_layer.action_cancel_valuation_out()
                    else:
                        stock_valuation_layer.action_cancel_valuation_in()
    
    def action_reset_draft(self):
        self.write({'line_ids': [(5,)],'state': 'draft'})

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_cancel(self):
        for move in self:
            siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
            move._do_unreserve()
            if move.propagate_cancel:
                if all(state == 'cancel' for state in siblings_states):
                    move.move_dest_ids._action_cancel()
            else:
                if all(state in ('done', 'cancel') for state in siblings_states):
                    move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                    move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
        self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
        return True

    def _do_unreserve(self):
        moves_to_unreserve = self.env['stock.move']
        for move in self:
            if move.state == 'cancel':
                moves_to_unreserve.mapped('move_line_ids').unlink()
                return True

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    def unlink(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for ml in self:
            if ml.product_id.type == 'product' and not ml.location_id.should_bypass_reservation() and not float_is_zero(ml.product_qty, precision_digits=precision):
                quant = self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id,package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                return quant
        return True
