

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    day = fields.Selection(selection=[
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miercoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sabado'),
        ], string='Day', copy=False, help='Visit Day.')
    sale_zone_id = fields.Many2one("partner.sale.zone", string="Sale Zone", domain="[('active', '=', True)]")
