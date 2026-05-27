# -*- coding: utf-8 -*-

from odoo import fields, models, api, tools,_
from odoo.exceptions import AccessError, UserError

class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'
    _description = 'Stock Landed Cost'

    account_move_count = fields.Integer(string='Moves Count', compute='_get_account_moves', readonly=True)

    
    def _get_account_moves(self):
        move_obj = self.env['account.move']
        self.account_move_count = move_obj.search_count(['|',
                                                         ('ref', 'like', self.account_move_id.name),
                                                         ('id', 'in', self.account_move_id.ids)])

    
    def action_view_account_moves(self):
        xml_id = 'account.view_move_tree'
        tree_view_id = self.env.ref(xml_id).id
        xml_id = 'account.view_move_form'
        form_view_id = self.env.ref(xml_id).id
        return {
            'name': _('Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'),
                      (form_view_id, 'form')],
            'res_model': 'account.move',
            'domain': ['|',
                       ('ref', 'like', self.account_move_id.name),
                       ('id', 'in', self.account_move_id.ids)],
            'type': 'ir.actions.act_window',
        }

    
    def button_cancel(self):
        for stock in self:
            print('unavez')
            """
            Henry validar si se realizo movimientos de productps antes de Cancelar el coste de destino
            """
            if not self.user_has_groups('sd_stock_valuation_layer.sd_stock_valuation_layer_group_cancelar_purchase'):
                if stock.valuation_adjustment_lines:
                    for valuation_adjustment_line in stock.valuation_adjustment_lines:
                        valor_valoracion_total =0
                        valor_costo_destino_total= 0
                        valuation_layer_picking = None
                        print('cuantas veces entra')
                        for valuation_layer_id in valuation_adjustment_line.move_id.stock_valuation_layer_ids:
                            if valuation_layer_id.stock_landed_cost_id:
                                """ valor de los costo de destino """
                                valor_costo_destino_total += valuation_layer_id.value
                            else:
                                """ valor del picking(compra) """
                                valor_valoracion_total += valuation_layer_id.value
                                valuation_layer_picking = valuation_layer_id
                        """ Validar si se realizo Movimientos del productos"""
                        if valuation_layer_picking:
                            print('int(valuation_layer_picking.remaining_value) ',int(valuation_layer_picking.remaining_value), ' int(valor_costo_destino_total+valor_valoracion_total) ',int(valor_costo_destino_total+valor_valoracion_total))
                            if not int(valuation_layer_picking.remaining_value) == int(valor_costo_destino_total+valor_valoracion_total):
                                raise UserError(_('No es posible cancelar una orden con Movimientos realizados, consulte a su soporte porfavor!!\n- forzar la cancelacion si es necesario y volver a reprocesar\nMotivos: Se realizo Ventas o salidas de este Costo de importación\nRecomendaciones: REPROCESAR!!'))

                        """
                        Si no se realizo ningun Movimiento entonces se continua con el proceso de Cancelar coste de destino
                        """



            stock.account_move_id.button_cancel()
            #for aml in stock.account_move_id : 

            #stock.account_move_id.unlink()
            
            for line in stock.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                    

                    remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
                    linked_layer = line.move_id.stock_valuation_layer_ids[:1]
                    # Prorate the value at what's still in stock
                    cost_to_add = (remaining_qty / line.move_id.product_qty) * line.additional_landed_cost



                    if not stock.company_id.currency_id.is_zero(cost_to_add):
                        valuation_layer = self.env['stock.valuation.layer'].search([('stock_valuation_layer_id','=',linked_layer.id)],order="id desc", limit=1)

                        
                        valuation_layer.write({'value' :valuation_layer.value -cost_to_add  })
                        linked_layer.remaining_value -= cost_to_add

                    """"
                    Henry
                    realizar un Unlink a todas las valoraciones de costo de destino"""
                    for stock_valuation_layer in line.move_id.stock_valuation_layer_ids:
                        if stock_valuation_layer.stock_landed_cost_id and stock_valuation_layer.stock_landed_cost_id.id == self.id:
                            stock_valuation_layer.sudo().unlink()

                    line.unlink()
        return self.write({'state': 'cancel'})


    
    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel'])
        return orders.write({
            'state': 'draft',
        })
