# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError, UserError
class InheritLandedCost(models.Model):

    _inherit = "stock.landed.cost"
    sd_date = fields.Datetime('Fecha', required=True, default=fields.Datetime.now)

    compute_field = fields.Boolean(string="check field", compute='get_user')

    @api.depends('compute_field')
    def get_user(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('sd_landed_cost_adjustment_inventory.sd_group_landed_cost_date'):
            self.compute_field = True
        else:
            self.compute_field = False

    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if vals['sd_date']:
                vals['name'] = self.env['ir.sequence'].with_context(ir_sequence_date=vals['sd_date']).next_by_code('stock.landed.cost')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.landed.cost')

        print(vals['name'],'------------nombre')
        return super(InheritLandedCost, self).create(vals)
    def button_validate(self):
        """ validar si La compra tiene Moviminetos -Henry"""
        # self.verificar_si_existe_movimientos_de_la_compra()
        if self.sd_date:
            self.update({'date': self.sd_date})
        res = super(InheritLandedCost, self).button_validate()
        """ Heredar Fecha - Henry"""

        if self.sd_date:
            self.heredar_fecha_valuation()
        return res

    def compute_landed_cost(self):
        res = super(InheritLandedCost, self).compute_landed_cost()
        self.compute_average_landed_cost()
        return res
    def heredar_fecha_valuation(self):
        """ Heredar Fecha a valoraciones"""
        date_inherit = self.sd_date
        for valuation_adjustment_line in self.valuation_adjustment_lines:
            for stock_valuation_layer in valuation_adjustment_line.move_id.stock_valuation_layer_ids:
                if stock_valuation_layer.stock_landed_cost_id and stock_valuation_layer.stock_landed_cost_id.id == self.id:
                    parametros = []
                    parametros.append(date_inherit)
                    parametros.append(stock_valuation_layer.id)
                    self.env.cr.execute("UPDATE public.stock_valuation_layer SET create_date=%s WHERE id=%s ", (parametros))

        """ heredar Fecha a Asiento contable"""
        for move_line in self.account_move_id:
            date_move = self.sd_date.date()
            move_line.write({
                'date': date_move
            })

            for line_id in move_line.line_ids:
                line_id.write({
                    'date': date_move
                })

            for line_id in move_line.invoice_line_ids:
                line_id.write({
                    'date': date_move
                })

    # def obtener_fecha_hora_actual(self):
    #     """ Obtener time actual  """
    #
    #     date_actual = fields.Datetime.now().strftime('%H:%M:%S')
    #     date_account = self.sd_date.strftime('%Y-%m-%d')
    #     date_inherit = date_account + ' ' + date_actual
    #     date_inherit = datetime.strptime(date_inherit, '%Y-%m-%d %H:%M:%S')
    #     return date_inherit
    def verificar_si_existe_movimientos_de_la_compra(self):
        """ Validar si la Entrada(compra) tiene Movimientos"""
        for picking_id in self.picking_ids:
            for move_line_id in picking_id.move_lines:
                if len(move_line_id.stock_valuation_layer_ids) > 1:
                    # Si existe movimientos tiene mas de dos valoraciones
                    valor_coste_destino = 0
                    valor_compra = 0
                    remaining_value = 0
                    for stock_valuation_layer_id in move_line_id.stock_valuation_layer_ids:
                        if stock_valuation_layer_id.stock_landed_cost_id:
                            valor_coste_destino += stock_valuation_layer_id.value
                        else:
                            valor_compra += stock_valuation_layer_id.value
                            remaining_value += stock_valuation_layer_id.remaining_value
                    if not (valor_coste_destino+valor_compra) == remaining_value:
                        raise UserError(
                            _('No es posible continuar,\nExisten Movientos realizados del producto "%s"\nde la compra "%s"') % (
                                move_line_id.product_id.name, move_line_id.picking_id.purchase_id.name))

                else:
                    for stock_valuation_layer_id in move_line_id.stock_valuation_layer_ids:
                        stock_valuation_layer_id.existen_movimientos_realizados()
    def action_inherit_date_force(self):
        if self.date:
            self.heredar_fecha_valuation()