# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError


class PartnerSaleZone(models.Model):
    _name = "partner.sale.zone"
    _description = "Partner sale zone"

    code = fields.Char()
    name = fields.Char(string="Zone", required=True)
    active = fields.Boolean(default=True)
