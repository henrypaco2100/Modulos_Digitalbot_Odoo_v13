# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
try:
    import simplejson as json
except ImportError:
    import json
import logging
import werkzeug
import requests
from odoo import http
from odoo.addons.web.controllers.main import Home,ensure_db
from odoo.http import request
_logger = logging.getLogger(__name__)


class WKHome(Home):

    def list_providers(self):
        try:
            domain = [('enabled', '=', True)]
            providers = request.env['auth.oauth.provider'].sudo().search_read(domain)
        except Exception:
            providers = []
        for provider in providers:
            return_url = request.httprequest.url_root + 'auth_oauth/signin'
            state = self.get_state(provider)
            params = dict(
                response_type='token',
                client_id=provider['client_id'],
                redirect_uri=return_url,
                scope=provider['scope'],
                state=json.dumps(state),
            )
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.url_encode(params))
        return providers

    def get_state(self, provider):
        redirect = request.params.get('redirect') or 'web'
        if not redirect.startswith(('//', 'http://', 'https://')):
            redirect = '%s%s' % (request.httprequest.url_root, redirect[1:] if redirect[0] == '/' else redirect)
        state = dict(
            d=request.session.db,
            p=provider['id'],
            r=werkzeug.url_quote_plus(redirect),
        )
        token = request.params.get('token')
        if token:
            state['t'] = token
        return state

    @http.route()
    def web_login(self, *args, **post):
        ensure_db()
        cr= request.cr
        default = request.env['ir.config_parameter'].sudo().get_param
        if default('odoo_captcha_login_lockdown.enabled_captcha'):
            max_error_attmept = default('odoo_captcha_login_lockdown.max_error_attmept') or 0
            if max_error_attmept:
                max_error_attmept = int(max_error_attmept)
            max_error_attmept =  max_error_attmept and max_error_attmept or 0
            failed_attem = request.session.get('failed_attem',0)

            if request.httprequest.method == 'POST' and  failed_attem>= max_error_attmept:
                    secret_key= default('odoo_captcha_login_lockdown.auth_captcha_secret_key')
                    captcha_result= self.verify_grecaptcha(post.get('g-recaptcha-response'),secret_key)
                    if not captcha_result.get("success", False):
                        request.params['login_success'] = False
                        values = request.params.copy()
                        values['error'] = self.custom_grecaptcha_error_message(captcha_result.get('error-codes', None))
                        values['recaptcha_security_enabel'] = True
                        values['providers']=self.list_providers()
                        if not failed_attem:failed_attem = 0
                        failed_attem+=1
                        request.session['failed_attem']=failed_attem
                        return request.render('web.login', values)

            result =  super(WKHome, self).web_login(*args, **post)
            if request.httprequest.method == 'GET' and failed_attem and (failed_attem>= max_error_attmept):
                result.qcontext.update({'error':"Please Don't forgot to validate CAPTCHA,Maximum Allowed Error Attempt [{max_error_attmept}] .".format(
                    max_error_attmept= max_error_attmept)}
                )
                result.qcontext.update({'recaptcha_security_enabel':True})

            if request.httprequest.method == 'POST'  :
                if result.qcontext.get('error'):
                    if not failed_attem:failed_attem = 0
                    failed_attem+=1
                    request.session['failed_attem']=failed_attem
                    request.params['login_success'] = False
                    if   failed_attem<max_error_attmept:
                        result.qcontext.update({'error':'{error},Login LockDown is Enabled  you have Left {attemp} Attempt!'.format(
                        error=result.qcontext.get('error'),attemp= max_error_attmept-failed_attem)}
                        )
                    else:
                        result.qcontext.update({'error':"Please Don't forget to validate CAPTCHA."})
                else:
                    failed_attem = None
                    request.params['login_success'] = True
                    request.session['failed_attem'] = failed_attem
                    result.qcontext.update({'recaptcha_security_enabel':None})

                if failed_attem and failed_attem>=max_error_attmept:
                    result.qcontext.update({'error':"Please Don't forgot to validate CAPTCHA,Maximum Allowed Error Attempt [{max_error_attmept}] .".format(
                        max_error_attmept= max_error_attmept)}
                    )
                    result.qcontext.update({'recaptcha_security_enabel':True})
            return result
        else:
            return  super(WKHome, self).web_login(*args, **post)

    def custom_grecaptcha_error_message(self,error_code):
        error_code_mapper={
            'missing-input-secret':'Secret parameter is missing,Please Inform the Site-Admin',
            'invalid-input-secret':'Secret parameter is invalid or malformed,Please Inform the Site-Admin.',
            'missing-input-response':'CAPTCHA is missing,Please Try Again.',
            'invalid-input-response':'CAPTCHA is missing is invalid or malformed,,Please Try Again.'
        }
        return error_code_mapper.get(error_code[0] if error_code else None,'Please Fill All Entry and Submit Recaptcha Again.')

    def verify_grecaptcha(self,response,secret_key ):
        url = "https://www.google.com/recaptcha/api/siteverify"
        params = {
            'secret':secret_key ,
            'response': response,
            'remoteip': self.get_client_ip()
        }
        verify_rs = requests.get(url, params=params, verify=True)
        verify_rs = verify_rs.json()
        return verify_rs

    def get_client_ip(self):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return base_url
