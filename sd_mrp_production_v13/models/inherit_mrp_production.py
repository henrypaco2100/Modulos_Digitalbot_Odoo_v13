from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError

class InheritFabricacionCosto(models.Model):
    _inherit = 'mrp.production'
    def duplicate(self,default=None):
        """ heredamos la funcion para duplciar orden de produccion y llamamos al nuevo formulariol"""
        res = self.copy()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'views': [[self.env.ref('mrp.mrp_production_form_view').id, 'form']],
            'res_id': res.id,
            'target': 'current',
        }


    """ QUitamos este codigo porque ya no Controlaremos el stock Disponible para producir"""
    # def open_produce_product(self):
    #     res = super(InheritFabricacionCosto, self).open_produce_product()
    #     self.comprabar_si_esta_assign()
    #     self.ensure_one()
    #     if self.bom_id.type == 'phantom':
    #         raise UserError(_('You cannot produce a MO with a bom kit product.'))
    #     action = self.env.ref('mrp.act_mrp_product_produce').read()[0]
    #     return res
    # def comprabar_si_esta_assign(self):
    #     for move_raw_id in self.move_raw_ids:
    #         if move_raw_id.state != 'assigned':
    #             raise UserError(_('No es Posible Continuar si no estan todos los Productos Disponible.'))
    # def button_unreserve(self):
    #     self.ensure_one()
    #     self.do_unreserve()
    #     res = super(InheritFabricacionCosto,self).button_unreserve()
    #     self.cambiar_estado_movimiento_y_quitar_reserva_stock_move_line()
    #     return res
    # def cambiar_estado_movimiento_y_quitar_reserva_stock_move_line(self):
    #     for lineas in self.move_raw_ids:
    #         if lineas.state == 'assigned' or lineas.reserved_availability >0:
    #             lineas.write({
    #                 'state':'waiting',
    #                 'reserved_availability':0,
    #             })
    #             for move_line in lineas.move_line_ids:
    #                 move_line.write({
    #                     'state':'waiting',
    #                     # 'product_uom_qty':0,
    #                 })
    # def copy(self,default=None):
    #     res=super(InheritFabricacionCosto, self).copy(default)
    #     return res

# class SdStockMoveMrp(models.Model):
#     _inherit = 'stock.move'
#
#     def _action_assign(self):
#         """
#         Funcion de Movimiento de existencias para realizar reservas
#         Heredamos y realizamos reservas por lote sodigitalim
#         """
#         res = super(SdStockMoveMrp, self)._action_assign()
#         for move in self.filtered(lambda x: x.production_id or x.raw_material_production_id):
#             for move_line in move.move_line_ids:
#                 if move_line.product_id.tracking == 'lot':
#                     move_line.lot_id.action_reservar_lot(move_line.product_uom_qty)
#         return res
#     def _do_unreserve(self):
#         """
#         Funcion de Movimiento de existencias para anular las reservas
#         heredamos y anulamos las reservas de los lotes
#         """
#         res = super(SdStockMoveMrp, self)._do_unreserve()
#         for move in self.filtered(lambda x: x.production_id or x.raw_material_production_id):
#             for move_line in move.move_line_ids:
#                 if move_line.product_id.tracking == 'lot':
#                     move_line.lot_id.do_unreserve_lot(move_line.product_uom_qty)
#
#         return res
# class SdStockMoveLineMrp(models.Model):
#     _inherit = 'stock.move.line'
#     sd_product_reserve_qty = fields.Float(string='Reservado por lote')





