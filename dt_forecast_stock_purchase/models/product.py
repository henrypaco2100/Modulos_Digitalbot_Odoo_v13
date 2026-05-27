# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2019 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fsp_qty_expected = fields.Float(
        string='Monthly quantity expected to sell',copy=False,tracking=True)
