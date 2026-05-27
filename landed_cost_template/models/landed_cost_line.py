# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


SPLIT_METHOD = [
    ('equal', 'Igual'),
    ('by_quantity', 'Por Cantidad'),
    ('by_current_cost_price', 'Por Costo Actual'),
    ('by_weight', 'Por Peso'),
    ('by_volume', 'Por Volumen'),
]


class CustomLandedCostLine(models.Model):
    _name = 'custom.landed.cost.lines'
    _description = 'Custom Landed Cost Line'


    name = fields.Char(
    	string='Descripción'
    )
    custom_template_id = fields.Many2one(
        'landed.cost.template',
        string='Plantilla de Coste en Destino',
        required=True,
        ondelete='cascade'
    )
    custom_product_id = fields.Many2one(
    	'product.product',
    	string='Producto',
    	required=True
    )
    custom_price_unit = fields.Float(
    	string='Costo',
    	digits='Precio Producto',
    	required=True
    )
    custom_split_method = fields.Selection(
    	SPLIT_METHOD, 
    	# string='Split Method',
        string ='Método de División',
    	required=True
    )
    custom_account_id = fields.Many2one(
    	'account.account',
    	string='Cuenta',
    	domain=[('deprecated', '=', False)]
    )


    @api.onchange('custom_product_id')
    def custom_onchange_product_id(self):
        if not self.custom_product_id:
            self.quantity = 0.0
        self.name = self.custom_product_id.name or ''
        self.custom_split_method = self.custom_split_method or 'equal'
        self.custom_price_unit = self.custom_product_id.standard_price or 0.0
        accounts_data = self.custom_product_id.product_tmpl_id.get_product_accounts()
        self.custom_account_id = accounts_data['stock_input']