from odoo import api, fields, models, _, tools

class SdInheritAccountMoveMerquimia(models.Model):
    _inherit = 'account.move'
    invoice_user_id = fields.Many2one(
        'res.users', string='Comercial', index=True, tracking=2, default=lambda self: self.env.user,
        domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id),('sd_comercial', '=', True)] )



