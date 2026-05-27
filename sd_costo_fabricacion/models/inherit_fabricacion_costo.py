from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError

class InheritFabricacionCostoStockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    st_costo_unit = fields.Float('done',compute='costo_unitario_valoracion_inventacio', default=0.0, digits='Costo Unitario', copy=False, readonly=True)
    st_costo_subtotal = fields.Float('done', default=0.0, digits='Subtotal', copy=False, readonly=True)

    @api.depends('qty_done')
    def costo_unitario_valoracion_inventacio(self):
        for line in self:
            id_move = line.move_id.id
            objeto_producion= line.move_id.production_id
            valoracion_intetario = line.env['stock.valuation.layer'].search([('stock_move_id','=',id_move)])
            if valoracion_intetario:
                for valoracion in valoracion_intetario:
                    line.update({
                        'st_costo_unit': round(valoracion.unit_cost,2),
                        'st_costo_subtotal':round(abs(valoracion.value),2)
                    })
                objeto_producion.hallar_costo_total_produccion()
            else:
                line.update({
                    'st_costo_unit':0.0,
                    'st_costo_subtotal': 0.0
                })


class InheritFabricacionCosto(models.Model):
    _inherit = 'mrp.production'

    st_costo_total = fields.Float(string='Total', readonly=True,)
    def hallar_costo_total_produccion(self):
        amount_total= 0
        for line in self.finished_move_line_ids:
            amount_total += line.st_costo_subtotal
        self.st_costo_total=round(amount_total,2)