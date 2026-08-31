# -*- coding: utf-8 -*-
from odoo import api, fields, models


class EsiCashFlow(models.Model):
    _name = 'esi.cash.flow'
    _description = 'ESI Cuenta de Flujo'
    _order = 'sequence, code, name'

    name = fields.Char(string='Nombre', required=True, index=True)
    code = fields.Char(string='Código', index=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    flow_type = fields.Selection([
        ('income', 'Ingreso'),
        ('expense', 'Egreso'),
    ], string='Tipo', required=True, default='expense', index=True)
    parent_id = fields.Many2one(
        'esi.cash.flow', string='Categoría superior', ondelete='restrict', index=True)
    child_ids = fields.One2many('esi.cash.flow', 'parent_id', string='Subcategorías')
    active = fields.Boolean(default=True)
    note = fields.Text(string='Notas')
    complete_name = fields.Char(
        string='Nombre completo', compute='_compute_complete_name', store=True)

    _sql_constraints = [
        ('code_company_uniq', 'unique(code)', 'El código de CTA Flujo debe ser único.'),
    ]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for rec in self:
            rec.complete_name = '%s / %s' % (rec.parent_id.complete_name, rec.name) if rec.parent_id else rec.name

    def name_get(self):
        result = []
        for rec in self:
            name = rec.complete_name or rec.name
            if rec.code:
                name = '[%s] %s' % (rec.code, name)
            result.append((rec.id, name))
        return result
