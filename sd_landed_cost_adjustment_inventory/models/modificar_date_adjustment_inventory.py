# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
# import datetime
from datetime import datetime
import pytz
from odoo.exceptions import UserError, ValidationError


class InheritInventoryLine(models.Model):
    _inherit = 'stock.inventory'
    compute_field = fields.Boolean(string="check field", compute='get_user')

    @api.depends('compute_field')
    def get_user(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('sd_landed_cost_adjustment_inventory.sd_group_adjustment_inventory'):
            self.compute_field = True
        else:
            self.compute_field = False
    def _action_start(self):
        date = self.date
        res = super(InheritInventoryLine,self)._action_start()
        self.write({
            'date': date
        })
        return res
    def action_validate(self):
        date = self.date
        res = super(InheritInventoryLine, self).action_validate()
        """ Heredar fechas David"""
        if date:
            self.date = date
            self.InheritDate()
        return res

    def InheritDate(self):
        date_inherit = self.date
        stock_move_lines = self.env['stock.move.line'].search([('move_id','in',self.move_ids.ids)])
        """ heredar Fecha movimientos de productos"""
        for stock_move_line in stock_move_lines:
            stock_move_line.sudo().write({
                'date': date_inherit
            })
        self.line_ids.write({
            'inventory_date':date_inherit
        })
        """ heredar para asientos contables """
        account_move = self.env['account.move'].search([('stock_move_id.id', 'in', self.move_ids.ids)])
        date_account = self.date.date()
        for account_move_line in account_move:
            account_move_line.write({
                'date': date_account
            })

            for account_line_id in account_move_line.line_ids:
                account_line_id.write({
                    'date': date_account
                })

            for account_invoice_line_id in account_move_line.invoice_line_ids:
                account_invoice_line_id.write({
                    'date': date_account
                })
        """ Heredar fecha movimientos de existencia y valoraciones"""
        for stock_move in self.move_ids:
            stock_move.sudo().write({
                'date': date_inherit,
                'date_expected': date_inherit,
            })
            for stock_valuation_layer in stock_move.stock_valuation_layer_ids:
                parametros = []
                parametros.append(date_inherit)
                parametros.append(stock_valuation_layer.id)
                self.env.cr.execute("UPDATE public.stock_valuation_layer SET create_date=%s WHERE id=%s ", (parametros))

    def obtener_fecha_hora_actual(self):
        """ Obtener time actual  """

        date_actual = fields.Datetime.now().strftime('%H:%M:%S')
        date_account = self.date.strftime('%Y-%m-%d')
        date_inherit = date_account + ' ' + date_actual
        date_inherit = datetime.strptime(date_inherit, '%Y-%m-%d %H:%M:%S')
        return date_inherit

    def action_inherit_date_force(self):
        if self.date:
            self.InheritDate()
