# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from collections import defaultdict
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_cancel(self):
        """ Cancels production order, unfinished stock moves and set procurement
        orders in exception """
        if not self.move_raw_ids:
            self.state = 'cancel'
            return True
        self._action_cancel()
        res = super(MrpProduction, self).action_cancel()
        self.cancelar_Sodigitalim()
        return res
    def cancelar_Sodigitalim(self):
        """  Esta Nueva logica se funciona con la anterior logica aumentando el rastreo de valoracion de entradas con salidas
        HENRY -DAVID
        """

        user = self.env['res.users'].has_group('st_cancel_production_order.group_production_cancel')
        if user == 1:
            #movimientos existencia Materia Prima
            if self.move_raw_ids:
                for movimiento_existencias in self.move_raw_ids:
                    # cancelar valoracion Inventario
                    for stock_valuation_layer in movimiento_existencias.stock_valuation_layer_ids:
                        if stock_valuation_layer:
                            # Henry VALUATION DETALLADA
                            if stock_valuation_layer.state == 'confirmed':
                                stock_valuation_layer.action_cancel_valuation_out()

                    #cancelar move.line moviento producto
                    for stock_move_line in movimiento_existencias.move_line_ids:
                        """
                        El Proceso de este Codigo lo realiza el metodo
                        stock_valuation_layer.sudo().unlink()
                        """

                        stock_move_line.write({
                            'state': 'cancel',
                            'qty_done':0,
                        })
                    for stock_valuation_layer in movimiento_existencias.stock_valuation_layer_ids:
                        if stock_valuation_layer:
                            stock_valuation_layer.sudo().unlink()
                    # cancelar asientos contables
                    for asientos_contables in movimiento_existencias.account_move_ids:
                        if asientos_contables:
                            asientos_contables.button_draft()
                            asientos_contables.button_cancel()

                    movimiento_existencias.write({'state': 'cancel'})


            #movimiento existencias producto Terminado
            if self.move_finished_ids:
                for movimiento_existencias_producido in self.move_finished_ids:

                    # cancelar valoracion Inventario
                    for stock_valuation_layer in movimiento_existencias_producido.stock_valuation_layer_ids:
                        if stock_valuation_layer:
                            # HENRY VALUATION DETALLADA
                            if stock_valuation_layer.state == 'confirmed':
                                stock_valuation_layer.action_cancel_valuation_in()

                    # cancelar move.line moviento producto
                    for stock_move_line in movimiento_existencias_producido.move_line_ids:
                        stock_move_line.write({
                            'state': 'cancel',
                            'qty_done': 0,
                        })
                    for stock_valuation_layer in movimiento_existencias_producido.stock_valuation_layer_ids:
                        if stock_valuation_layer:
                            stock_valuation_layer.sudo().unlink()

                    # cancelar asientos contables
                    for asientos_contables in movimiento_existencias_producido.account_move_ids:
                        if asientos_contables:
                            asientos_contables.button_draft()
                            asientos_contables.button_cancel()

                    movimiento_existencias_producido.write({'state': 'cancel'})




