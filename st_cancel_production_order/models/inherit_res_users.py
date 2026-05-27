# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields


class Users(models.Model):
    _inherit = 'res.users'

    cancel_id_prod = fields.Boolean('Cancel Production Order')





