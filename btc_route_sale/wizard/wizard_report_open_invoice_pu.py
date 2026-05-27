import base64

from dateutil.relativedelta import relativedelta
from odoo import api, models, fields, _
from odoo.exceptions import Warning, UserError
from datetime import date, datetime, timedelta


class WizardReportOpenInvoicePu(models.TransientModel):
    _name = "wizard.report.open.invoice.pu"
    _description = "Get Report Open Invoice Purchase"

    start_date = fields.Date(string="Start Date",
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    end_date = fields.Date(string="End Date", default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    company_id = fields.Many2one('res.company', default=lambda x: x.env.company)
    partner_id = fields.Many2one('res.partner')
    branch_id = fields.Many2one('company.branches')
    user_id = fields.Many2one('res.users')
    sale_zone_id = fields.Many2one("partner.sale.zone", string="Zone")
    day = fields.Selection(selection=[
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miercoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sabado'),
    ], string='Day', help='Visit Day.')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and not self.end_date:
            self.end_date = self.last_day_of_month(date(int(self.start_date.year), int(self.start_date.month), 1))
            print(str(self.end_date))

    def get_report(self):
        format = "%Y-%m-%d"
        if datetime.strptime(str(self.end_date), format) < datetime.strptime(str(self.start_date), format):
            raise Warning("End date should be lower than start date")

        data = {}
        data["start_date"] = str(self.start_date)
        data["end_date"] = str(self.end_date)
        # data["company_id"] = str(self.company_id.id)
        data["partner_id"] = str(self.partner_id.id)
        data['report_def_obj'] = self.name

        self.env['report.result'].generate_report(data)

    def last_day_of_month(self, any_day):
        next_month = any_day.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)

    def generate_report(self):
        self.ensure_one()

        domain = [('company_id', '=', self.company_id.id)]
        domain += [('state', '=', 'posted')]
        domain += [('state', '!=', 'draft')]
        #domain += [('state_factura', '=', 'V')]
        #domain += [('move_type', '=', 'out_invoice')]
        domain += [('move_type', 'in', ('in_invoice', 'in_receipt'))]
        domain += [('payment_state', '!=', 'paid')]
        domain += [('payment_state', '!=', 'reversed')]
        #domain += [('date', '>=', self.start_date), ('date', '<=', self.end_date), ('state', '=', 'posted')]
        if self.branch_id:
            domain += [('branch_id.id', '=', self.branch_id.id)]
        if self.user_id:
            domain += [('user_id.id', '=', self.user_id.id)]
        if self.day:
            domain += [('day', '=', self.day)]
        if self.partner_id:
            domain += [('partner_id.id', '=', self.partner_id.id)]
        if self.sale_zone_id:
            domain += [('sale_zone_id.id', '=', self.sale_zone_id.id)]

        obj_invoices = self.env['account.move'].search(domain).sorted(key=lambda r: r.partner_id).ids
        rp_payment_sale_id = self.env['rp.open.invoice.report.pu'].create({
            'invoice_ids': [(6, False, obj_invoices)],
            'company_id': self.company_id.id,
            'start_date': self.start_date,
            'end_date': self.end_date
        })
        if self._context.get('excel_report'):
            data_value = {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'day': self.day,
                'partner_id': self.partner_id.id,
                'user_id': self.user_id.id,
                'branch_id': self.branch_id.id,
                'sale_zone_id': self.sale_zone_id.id,
                'domain': domain,
                'company_id': self.company_id.id
            }
            report_name = 'report_xlsx.rp_invoice_open_pu_xlsx'
            return (
                self.env["ir.actions.report"]
                    .search(
                    [("report_name", "=", report_name), ("report_type", "=", 'xlsx')],
                    limit=1,
                ).report_action(self, data=data_value)
            )
        else:
            return self.env.ref('btc_route_sale.invoice_open_report_btc_pu').report_action(rp_payment_sale_id)


class RpPaymentSalePu(models.TransientModel):
    _name = "rp.open.invoice.report.pu"
    _description = 'Open Invoice Report Purchase'
    _order = 'name desc,date desc'

    invoice_ids = fields.Many2many('account.move', 'pu_move_id')
    name = fields.Char()
    company_id = fields.Many2one('res.company')
    has_invoices = fields.Boolean(default=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def get_amount_currency_company(self, amount=0, currency=None):
        company_id = self.env.company
        amount_currency = 0.00
        if amount > 0 and currency:
            if company_id.currency_id.id != currency.id:
                amount_currency = amount / currency.rate
            else:
                amount_currency = amount
        return amount_currency

    def get_days_difference(self, date_begin=None, date_end=None):
        self = self.with_company(self.company_id)
        today = fields.Date.context_today(self)
        if not date_begin:
            date_begin = today
        if not date_end:
            date_end = today
        diff_days = (date_end - date_begin).days
        return diff_days

    def get_sale_journal(self):
        journal_ids = []
        journal_ids = self.env['account.journal'].search([('type', '=', 'sale')])
        return journal_ids


