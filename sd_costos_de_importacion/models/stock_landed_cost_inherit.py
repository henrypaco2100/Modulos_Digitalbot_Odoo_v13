 # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError

#DAVID MODELO HEREDADO PARA PODER AGREGAR MAS CAMPOS A LA VISTA DE MOVIMIENTO DE PRODUCTOS


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'
    id_invoice_lc = fields.Many2many('account.move', string='Facturas LC')
    id_purchase = fields.Many2many('purchase.order',string='Compras')
    def button_validate_lc(self):
        array_product =[]
        # AL :
        if not self.vendor_bill_id : raise UserError(_("No existe ninguna factura. por favor crear una"))
        if self.vendor_bill_id.sd_nro_importacion: nro_importacion = self.vendor_bill_id.sd_nro_importacion
        elif self.id_purchase.sd_numero_importacion: nro_importacion = self.id_purchase.sd_numero_importacion
        else: nro_importacion = self.env['purchase.order'].search([('name','=',self.vendor_bill_id.invoice_origin)]).sd_numero_importacion
        if not nro_importacion: raise UserError(_("No existe ningun numero de importacion asociada a la compra origen \n Por favor Adicionar un numero de importacion a su compra gracias."))
        facturas = self.env['account.move'].search([('sd_nro_importacion', '=', nro_importacion),('name', '!=', self.vendor_bill_id.name ),('state','=','posted')])
        if len(facturas) >= 1:
            if len(self.id_invoice_lc) == len(facturas):raise UserError(_("Ya no hay facturas para adicionar"))
            else:
                self.update({
                    'id_invoice_lc': facturas,
                })
        # End AL
                ids = self.id_invoice_lc
                if ids and len(ids) > 0:
                    lc_lines = self.cost_lines
                    # for para cargar los productos de las lineas del costo destino or landed cost
                    for line in lc_lines:
                        array_product.append(line.product_id)
                    # for que carga la factura de compra en el coste destino
                    for line in ids:
                        for lines in line.invoice_line_ids.filtered(lambda x: x.is_landed_costs_line == True and x.product_id not in array_product):
                            vals = {
                                'product_id': lines.product_id.id,
                                'name': lines.name,
                                'account_id': lines.account_id.id,
                                'split_method': 'by_current_cost_price',
                                'price_unit': lines.price_subtotal,
                                'cost_id': self.id,
                            }
                            lc_lines.sudo().create(vals)
        else:
            raise UserError(_("Por Favor Adicionar una Factura"))