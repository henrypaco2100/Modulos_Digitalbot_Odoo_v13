import base64

from dateutil.relativedelta import relativedelta
from odoo import api, models, fields, _
from odoo.exceptions import Warning, UserError
from datetime import date, datetime, timedelta


class WizardGetReportPaymentCustomBcl(models.TransientModel):
    _name = "wizard.get.report.payment.custom.bcl"
    _description = "Get Report"

    start_date = fields.Date(string="Start Date",
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    end_date = fields.Date(string="End Date", default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    company_id = fields.Many2one('res.company', default=lambda x: x.env.company)
    partner_id = fields.Many2one('res.partner')
    user_id = fields.Many2one('res.users')
    branch_id = fields.Many2one('company.branches')
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
        # define data that tdo generate report
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
        cr = self.env.cr
        domain = [('company_id', '=', self.company_id.id)]
        domain += [('move_type', '=', 'out_invoice')]
        domain += [('state_factura', '=', 'V')]
        domain += [('payment_state', 'in', ['paid', 'partial'])]
        domain += [('date', '>=', self.start_date), ('date', '<=', self.end_date), ('state', '=', 'posted')]
        filters = ""
        if self.user_id:
            domain += [('user_id.id', '=', self.user_id.id)]
        if self.branch_id:
            domain += [('branch_id.id', '=', self.branch_id.id)]
        if self.sale_zone_id:
            domain += [('sale_zone_id.id', '=', self.sale_zone_id.id)]
        if self.day:
            domain += [('day', '=', self.day)]

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
            report_name = 'report_xlsx.rp_payment_sale_bleichner_xlsx'
            return (
                self.env["ir.actions.report"]
                    .search(
                    [("report_name", "=", report_name), ("report_type", "=", 'xlsx')],
                    limit=1,
                ).report_action(self, data=data_value)
            )
        else:
            if self.partner_id:
                filters += ' AND l.partner_id={}'.format(self.partner_id.id)
            arg_list = (self.start_date, self.end_date)
            query = '''
                SELECT r.id ,r.debit_move_id, r.credit_move_id, r.max_date,mv.state_factura,mv.payment_reference,mv.amount_total
                FROM account_partial_reconcile r inner join account_move_line l on r.credit_move_id=l.id
                inner join account_move mv on mv.id=l.move_id
                where r.amount >0.1 AND l.date BETWEEN %s and %s 
                and mv.state_factura not in ('A','N')  and mv.move_type in ('entry','out_invoice','out_receipt') 
                 and not l.partner_id is null
                 ''' + filters + '''
                 Order by l.date asc;
                '''

            print(query)
            cr.execute(query, arg_list)
            partial_reconciles = cr.dictfetchall()
            partial_reconcile_ids = [reconcile['id'] for reconcile in partial_reconciles if reconcile['id']]
            data = []
            for reconcile_id in partial_reconcile_ids:
                obj_reconcile = self.env["account.partial.reconcile"].search([('id', '=', reconcile_id)], limit=1)
                if self.day:
                    if self.day != obj_reconcile.debit_move_id.move_id.day:
                        continue
                if self.user_id:
                    if self.user_id != obj_reconcile.debit_move_id.move_id.user_id:
                        continue
                if self.branch_id:
                    if self.branch_id != obj_reconcile.debit_move_id.move_id.branch_id:
                        continue
                if self.sale_zone_id:
                    if self.sale_zone_id != obj_reconcile.debit_move_id.move_id.sale_zone_id:
                        continue
                rp_payment_sale_id = self.env['rp.payment.sale.route.line'].create({
                    'account_partial_reconcile_id': obj_reconcile.id,
                    'move_line_id_debit': obj_reconcile.debit_move_id.id,
                    'move_id_debit': obj_reconcile.debit_move_id.move_id.id,
                    'move_line_id_credit': obj_reconcile.credit_move_id.id,
                    'move_id_credit': obj_reconcile.credit_move_id.move_id.id,
                })
                data.append(rp_payment_sale_id.id)
                print(str(reconcile_id))
            rp_payment_sale_id = self.env['rp.payment.sale.route'].create({
                'payment_sale_lines': [(6, False, data)],
                'company_id': self.company_id.id,
                'start_date': self.start_date,
                'end_date': self.end_date
            })
            return self.env.ref('btc_route_sale.payment_sale_report_btc_v2').report_action(rp_payment_sale_id)


class RpPaymentSaleRoute(models.TransientModel):
    _name = "rp.payment.sale.route"
    _description = 'Payment Sale Route'
    _order = 'name desc,date desc'

    invoice_ids = fields.Many2many('account.move', 'invoice_id_rel_rp_sale_route')
    payment_sale_lines = fields.Many2many('rp.payment.sale.route.line', 'payment_sale_line_rel_rp_sale_route')
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


class RpPaymentSaleRouteLine(models.TransientModel):
    _name = "rp.payment.sale.route.line"
    _description = 'Payment Sale Route Line'

    account_partial_reconcile_id = fields.Many2one('account.partial.reconcile')
    move_line_id_debit = fields.Many2one('account.move.line', string="Move Line Debit")
    move_id_debit = fields.Many2one('account.move', string="Move Debit")
    move_line_id_credit = fields.Many2one('account.move.line', string="Move Line Credit")
    move_id_credit = fields.Many2one('account.move', string="Move Credit")
