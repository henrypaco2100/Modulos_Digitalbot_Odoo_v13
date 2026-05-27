# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
# DAVID: Modelo para la creacion de un campo de costo para el ajuste de Inventario.
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

# Extension del modelo de stock Inventory para añadir en su logica el proceso de actualizacion de los costos


class CostSupplier(models.Model):

    _name = "cost.supplier"
    _description = "Costo Compra"

    sequence = fields.Integer(default=10)

    partner_id = fields.Many2one('res.partner', string="Proveedor", required=True)

    date_cuotation = fields.Date(string="Fecha Cotizacion", required=True)

    product_ids = fields.Many2one('product.product', string="Producto", required=True)

    price = fields.Float(string="Precio Cotizado", default=0.0, required=True)

    quantity = fields.Integer(string="Cantidad", default=0)

    obs_text = fields.Text('Observaciones', help='Write here all supplementary information relative to this contract', copy=False)

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)




