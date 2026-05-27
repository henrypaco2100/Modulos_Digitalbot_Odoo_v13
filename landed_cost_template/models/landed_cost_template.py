# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LandedCostTemplate(models.Model):
    _name = 'landed.cost.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Landed Cost Template'
    
    name = fields.Char(
        string='Nombre',
        required=True,
    )
    custom_line_ids = fields.One2many(
        'custom.landed.cost.lines',
        'custom_template_id',
        string="Costo de líneas",
    )