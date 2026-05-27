from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
from datetime import date, datetime, timedelta


class AccountMove(models.Model):
    _inherit = "account.move"

    day = fields.Selection(selection=[
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miercoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sabado'),
        ], string='Day', help='Visit Day.')
    sale_zone_id = fields.Many2one("partner.sale.zone", string="Sale Zone")
    partner_ref = fields.Char(related='partner_id.partner_code', string='Reference')
    amount_paid_tmp = fields.Monetary(compute='_compute_amount_paid_tmp', string='Amount Paid', store=True)
    due_days_rute = fields.Integer(compute='_compute_due_days_route', string='Days')
    is_account_receivable = fields.Boolean(default=False)
    is_account_payable = fields.Boolean(default=False)

    @api.onchange('partner_id')
    def _partner_onchange(self):
        if self.partner_id:
            self.day = self.partner_id.day or False
            self.sale_zone_id = self.partner_id.sale_zone_id.id or False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('partner_id'):
                partner_id = self.env['res.partner'].search([('id', '=', vals.get('partner_id'))])
                if partner_id:
                    vals['day'] = partner_id.day or False
                    vals['sale_zone_id'] = partner_id.sale_zone_id.id or False
        return super(AccountMove, self).create(vals_list)

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount_paid_tmp(self):
        for rec in self:
            paid_amount = 0.0
            rec.amount_paid_tmp = rec.amount_total - rec.amount_residual
            if rec.amount_paid_tmp < 0:
                rec.amount_paid_tmp = paid_amount

    def get_sale_journal(self):
        journal_ids = []
        if self.journal_id:
            journal_ids = self.env['account.journal'].search([('type', '=', 'sale')])
        return journal_ids

    @api.model
    def _compute_due_days_route(self):
        for rec in self:
            self = self.with_company(self.company_id)
            today = fields.Date.context_today(self)
            date_begin = rec.invoice_date_due or today
            diff_days = (today - date_begin).days
            rec.due_days_rute = diff_days
