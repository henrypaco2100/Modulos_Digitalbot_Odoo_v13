# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
from odoo import fields,models,api
import logging

_log = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enabled_captcha = fields.Boolean(
        string="Enabled CAPTCHA Login LockDown",
        config_parameter='odoo_captcha_login_lockdown.enabled_captcha'
    )
    max_error_attmept =  fields.Integer(
        string="Max Error Attempt",
        help="Max Attempt After Login Will LockDown & Captcha will enabled ",
        config_parameter='odoo_captcha_login_lockdown.max_error_attmept' 
    )
    auth_captcha_secret_key = fields.Char(
        string = "Captcha Secret Key",
        help="Place Your CAPTCHA Secret Key",default='12345',
        config_parameter='odoo_captcha_login_lockdown.auth_captcha_secret_key' 
    )
    auth_captcha_site_key = fields.Char(
        string = "Captcha Site Key",
        help="Place Your CAPTCHA Site/Public Key",default='12345',
        config_parameter='odoo_captcha_login_lockdown.auth_captcha_site_key' 
    )
    @api.model
    def enable_captcha(self):
        enable_env = self.env['res.config.settings'].create({
                'enabled_captcha'           :   True,
                'max_error_attmept'         :   2,
                'auth_captcha_site_key'     :   '6LezXLEUAAAAAFr7N54rWMgD5m5dDDlBrqZjrF2R',
                'auth_captcha_secret_key'   :   '6LezXLEUAAAAAGZcT7JSUltl_sWqypHsKJMtmxU7',
            })
        enable_env.execute()