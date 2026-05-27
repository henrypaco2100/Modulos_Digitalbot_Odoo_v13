# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models

class TxtReport(models.TransientModel):
    _name = 'txt.report'

    txt_filename = fields.Char()
    txt_binary = fields.Binary( size=64)
