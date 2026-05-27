# -*- coding: utf-8 -*-

import datetime 

from odoo import models, fields , _
from odoo.exceptions import UserError


class CustomLandedCostWizard(models.TransientModel):
    _name = 'custom.landed.cost.wizard'
    _description = 'custom.landed.cost.wizard'

    custom_templ_id = fields.Many2one(
        'landed.cost.template',
        string='Seleccionar plantilla',
        required=True
    )

    def action_custom_load(self):
        stock_id = self.env['stock.landed.cost'
            ].browse(self._context.get('active_ids'))
        if self.custom_templ_id.custom_line_ids:
            for line in self.custom_templ_id.custom_line_ids:
                custom_line_vals = {
                                   'product_id': line.custom_product_id.id,
                                   'name' : line.name,
                                   'account_id': line.custom_account_id.id,
                                   'split_method': line.custom_split_method,
                                   'price_unit': line.custom_price_unit
                                            }
                stock_id.write({ 'cost_lines': [(0,0, custom_line_vals)],
            })



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
