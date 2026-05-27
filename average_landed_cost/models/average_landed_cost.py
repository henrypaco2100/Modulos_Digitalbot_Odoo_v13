
from odoo import fields, models, _
from odoo.exceptions import UserError


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    avg_landed_cost_lines = fields.One2many('average.landed.cost.lines',
                                            'line_id', string='Linea de Orden')

    def compute_average_landed_cost(self):
        """
        Calcular nuevo costo del producto
        """
        self.avg_landed_cost_lines.sudo().unlink()
        groups_coste = self.valuation_adjustment_lines.read_group([('move_id','in',self.valuation_adjustment_lines.mapped('move_id').ids)], ['additional_landed_cost:sum','former_cost:avg'], ['move_id'])
        valor_factura_comercial = 0
        gasto_importacion = 0
        for group in groups_coste:
            valor_factura_comercial += group['former_cost']
            gasto_importacion += group['additional_landed_cost']
        for group in groups_coste:
            move_id = self.env['stock.move'].browse(group['move_id'][0])
            self.avg_landed_cost_lines.create({
                'product_id': move_id.product_id.id,
                'quantity': move_id.product_uom_qty,
                'cost_porcent':(gasto_importacion/valor_factura_comercial)+1,
                'cost_product': group['former_cost'] / move_id.product_uom_qty,
                'costo_destino_producto': group['additional_landed_cost'],
                'average_landed_cost': group['additional_landed_cost'] / move_id.product_uom_qty,
                'cost_landed_unit': (group['additional_landed_cost'] + group['former_cost'])/move_id.product_uom_qty,
                'sd_total_producto': group['additional_landed_cost'] + group['former_cost'],
                'line_id': self.id
            })


class AverageLandedCostLines(models.Model):
    _name = 'average.landed.cost.lines'
    _description = 'Average Landed cost Lines'
    line_id = fields.Many2one('stock.landed.cost')
    product_id = fields.Many2one('product.product', 'Producto', required=True)
    quantity = fields.Integer('Cantidad')
    additional_landed_cost_sum = fields.Float('Sum')
    average_landed_cost = fields.Float('costo de Destino Unitario')
    #David
    cost_landed_unit = fields.Float('Nuevo Costo Unitario')
    cost_product = fields.Float('Costo Unitarioaaaa')
    cost_porcent = fields.Float('%')
    costo_destino_producto = fields.Float('costo destino por Producto')
    sd_total_producto = fields.Float('Costo Total Prod')
