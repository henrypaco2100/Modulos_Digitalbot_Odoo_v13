# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Website Captcha Login Lockdown",
  "summary"              :  """ODOO Website CAPTCHA Login LockDown : ODOO PlugIn For Providing Cyber Security ,Now Use CAPTCHA To  Get Protected Against  Cyber Threats .""",
  "category"             :  "Website",
  "version"              :  "3.0.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "maintainer"           :  "Prakash Kumar",
  "website"              :  "https://store.webkul.com/Odoo-Website-CAPTCHA-Log-In-LockDown.html",
  "description"          :  """https://webkul.com/blog/odoo-website-captcha-log-in-lockdown
  ODOO Website CAPTCHA Log-In LockDown : ODOO PlugIn For Providing Cyber Security ,Now Use CAPTCHA To  Get Protected Against  Cyber Threats""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=odoo_captcha_login_lockdown",
  "depends"              :  ['auth_signup'],
  "data"                 :  [
                             'views/template.xml',
                             'views/res_config.xml',
                            ],
  "demo"                 :  ['demo/res_config_demo.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "price"                :  25,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}