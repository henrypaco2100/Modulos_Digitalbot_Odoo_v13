 # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _



#LUIS MODELO HEREDADO PARA PODER AGREGAR MAS CAMPOS A LA VISTA DE MOVIMIENTO DE PRODUCTOS


class KardexValuateLines(models.Model):
    _name = 'kardex.valuate.lines'
    _description = "Vista Tree para el los campos De Kardex Fisico Valorado"

    """DAVID=Se coloca este campo currency_id para que se pueda manejar el currency de la compañia ya que sin esto sale error 
    al querer agregar un campo de tipo monetario"""

    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company)
    product_id = fields.Char('Producto', readonly=True)
    qty_done = fields.Float('Cantidad', default=0.0, readonly=True)
    date = fields.Datetime('Date', default=fields.Datetime.now, readonly=True)
    location_id = fields.Char('Desde', readonly=True)
    location_dest_id = fields.Char('Hasta', readonly=True)

    state_id = fields.Char(string="Estado", readonly=True)

    reference = fields.Char(string="Referencia", readonly=True)

    currency_id = fields.Many2one('res.currency', 'Currency', related='company_id.currency_id', readonly=True,
                                  required=True)

    cost_valuation = fields.Monetary(string="Valoracion Unitario",
                                     readonly=True)

    cost_valuation_total = fields.Monetary(string="Valoracion Total",
                                           readonly=True)

    landed_cost_unit = fields.Float(string="Cost Landed Unit")

    landed_cost_saldo = fields.Float(string="Cost Landed Saldo")

    line_id = fields.Many2one('stock.move.line')

    def search_lines_stock_move_lines(self):

        stock_moves_lines = self.env['stock.move.line'].filtered(lambda s: s.state != 'cancel')
        # stock_moves_lines.search([('line_id', 'in', self.ids)]).unlink()

        for line in stock_moves_lines:

            self.avg_landed_cost_lines.create({
                'date': line.date,
                'reference': line.reference,
                'product_id': line.product_id.name,
                'location_id': line.location_id.name,
                'location_dest_id': line.location_dest_id.name,
                'qty_done': line.qty_done,
                'cost_valuation': line.move_id.stock_valuation_layer_ids.unit_cost[0],
                'cost_valuation_total': line.move_id.stock_valuation_layer_ids.value[0],
                'state_id': line.state,
            })
            # return True

