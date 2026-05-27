from odoo import api, fields, models, tools

class InheritAccountMoveOrderLine(models.Model):
    _inherit = 'account.move'

#   para asegurar que el metodo este registrado despues de la primera herencia de account.move
#   se hizo que el modulo sd_plural_v13 dependa del modulo sd_comprobantes_contable
    @api.model
    def return_order_line_ids(self):
        order_line_by_id = super(InheritAccountMoveOrderLine, self).return_order_line_ids()
        order_line = sorted(order_line_by_id, key=lambda l: l.sequence)
        return order_line

    @api.onchange('ref')
    def _compute_name(self):
        for move in self:
            if move.sd_tipo == 'entry':
                move.line_ids.name = move.ref
