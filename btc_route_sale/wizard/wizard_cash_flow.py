import base64

from dateutil.relativedelta import relativedelta
from odoo import api, models, fields, _
from odoo.exceptions import Warning, UserError
from datetime import date, datetime, timedelta
import json


class WizardCashFlow(models.TransientModel):
    _name = "wizard.cash.flow"
    _description = "Get Cash Flow"

    start_date = fields.Date(string="Start Date",
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    end_date = fields.Date(string="End Date", default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    sd_rango = fields.Boolean('Rango')
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
        domain += [('payment_state', '!=', 'reversed')]
        # domain += [('date', '>=', self.start_date), ('date', '<=', self.end_date), ('state', '=', 'posted')]
        # if self.start_date:
        #    domain += [('date', '>=', self.start_date), ('date', '<=', self.start_date)]
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
        domain_invoice = domain.copy()
        domain_receipt = domain.copy()
        domain_payment = domain.copy()
        if self.sd_rango:
            domain_invoice += [('invoice_date', '>=', self.start_date),('invoice_date', '<=', self.end_date)]
            domain_receipt += [('invoice_date', '>=', self.start_date),('invoice_date', '<=', self.end_date)]
        else:
            domain_invoice += [('invoice_date', '=', self.start_date)]
            domain_receipt += [('invoice_date', '=', self.start_date)]

        domain_invoice += [('move_type', '=', 'out_invoice')]
        out_invoices = self.env['account.move'].search(domain_invoice)
        total_invoice = sum(rec.amount_total for rec in out_invoices)
        # print('total_invoice',total_invoice)
        count_invoice = len(out_invoices)
        domain_receipt += [('move_type', '=', 'out_receipt')]
        domain_receipt += [('invoice_payments_widget', 'not ilike', 'Reversi')]
        out_receipts_obj = self.env['account.move'].search(domain_receipt)
        out_receipts_id = []
        for rec in out_receipts_obj:
            if rec.invoice_payments_widget:
                data = rec.invoice_payments_widget
                if 'Reversi' not in data:
                    out_receipts_id.append(rec.id)
            else:
                out_receipts_id.append(rec.id)
        out_receipts = self.env['account.move'].browse(out_receipts_id)
        total_receipt = sum(rec.amount_total for rec in out_receipts)
        # print('total_receipt',total_receipt)
        count_receipt = len(out_receipts)

        #obj_invoices = self.env['account.move'].search(domain).sorted(key=lambda r: r.partner_id).ids
        # obj_invoices = self.env['account.move'].search(
        #     [('state', '=', 'posted'), ('state', '!=', 'draft'), ('move_type', '=', 'out_invoice'),
        #      ('payment_state', '!=', 'paid'), ('payment_state', '!=', 'reversed')]).sorted(key=lambda r: r.partner_id).ids
        # TODO invoices and receipt
        move_ids = []
        for rec in out_invoices.ids:
            move_ids.append(rec)
        for rec in out_receipts.ids:
            move_ids.append(rec)

        # TODO payments
        domain_payment += [('journal_id.type', 'in', ('bank', 'cash'))]
        if self.sd_rango:
            domain_payment += [('date', '>=', self.start_date), ('invoice_date', '<=', self.end_date)]
        else:
            domain_payment += [('date', '=', self.start_date)]
        payments_ids = self.env['account.move'].search(domain_payment)

        move_pay_ids = []
        for rec in payments_ids.ids:
            move_pay_ids.append(rec)
        print('rnago', self.sd_rango)
        rp_payment_sale_id = self.env['rp.cash.flow'].create({
            'invoice_ids': [(6, False, move_ids)],
            'company_id': self.company_id.id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'total_invoice': total_invoice,
            'count_invoice': count_invoice,
            'total_receipt': total_receipt,
            'count_receipt': count_receipt,
            'payment_ids': [(6, False, move_pay_ids)],
            'sd_rango': self.sd_rango,
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
                'company_id': self.company_id.id,
                'sd_rango': self.sd_rango,
            }
            report_name = 'report_xlsx.rp_invoice_open_xlsx'
            return (
                self.env["ir.actions.report"]
                    .search(
                    [("report_name", "=", report_name), ("report_type", "=", 'xlsx')],
                    limit=1,
                ).report_action(self, data=data_value)
            )
        else:
            return self.env.ref('btc_route_sale.cash_flow_report_btc').report_action(rp_payment_sale_id)

    def get_sales(self, domain=None):
        res = 2
        return res
    
 


class RpCashFlow(models.TransientModel):
    _name = "rp.cash.flow"
    _description = 'Cash Flow'
    _order = 'name desc,date desc'

    invoice_ids = fields.Many2many('account.move', 'rcf_move_id')
    name = fields.Char()
    company_id = fields.Many2one('res.company')
    has_invoices = fields.Boolean(default=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    sd_rango = fields.Boolean('Rango')
    # TODO section 1
    total_invoice = fields.Float(string="Total Invoice")
    total_receipt = fields.Float(string="Total Receipt")
    count_invoice = fields.Integer(string="Count Invoice")
    count_receipt = fields.Integer(string="Count Receipt")
    # TODO section 2
    payment_ids = fields.Many2many('account.move', 'rcp_move_id')
    # debits = fields.Many2many('account.move.line', 'invoice_ids')


    def get_amount_currency_company(self, amount=0, currency=None):
        company_id = self.env.company
        amount_currency = 0.00
        if amount > 0 and currency:
            if company_id.currency_id.id != currency.id:
                amount_currency = amount / currency.rate
            else:
                amount_currency = amount
        return amount_currency

    def get_values_to_incomes(self):
        
        if self.sd_rango:
            val_income = self.env['account.move.line'].search(
                [('name_number', 'like', 'ING%'), ('journal_id.type', 'in', ('bank', 'cash')), ('debit', '>', 0),
                 ('credit', '=', 0), ('date', '>=', self.start_date),('date', '<=', self.end_date), ('company_id', '=', 1),
                 ('move_id.state', '=', 'posted'), ('move_id.state', '!=', 'draft'),
                 ('move_id.payment_state', '!=', 'reversed')])
            grouped_partners = val_income.read_group(
                [('name_number', 'like', 'ING%'), ('journal_id.type', 'in', ('bank', 'cash')), ('debit', '>', 0),
                 ('credit', '=', 0), ('date', '>=', self.start_date),('date', '<=', self.end_date), ('company_id', '=', 1),
                 ('move_id.state', '=', 'posted'), ('move_id.state', '!=', 'draft'),
                 ('move_id.payment_state', '!=', 'reversed')], ['account_id', 'debit'], ['account_id', 'debit'])

        else:    
            val_income = self.env['account.move.line'].search([('name_number','like','ING%'),('journal_id.type', 'in', ('bank', 'cash')),('debit','>',0),('credit','=',0),('date','=',self.start_date),('company_id', '=', 1),('move_id.state', '=', 'posted'),('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')])
            grouped_partners = val_income.read_group([('name_number','like','ING%'),('journal_id.type', 'in', ('bank', 'cash')),('debit','>',0),('credit','=',0), ('date','=',self.start_date),('company_id', '=', 1),('move_id.state', '=', 'posted'), ('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')],  ['account_id', 'debit'], ['account_id', 'debit'])
        
        move_income_ids = []
        diary_id = ''
        for rects in grouped_partners:
            val_account = rects['account_id'][0]
            if val_account:
                payments_account = self.env['account.account'].search([('id', '=', val_account)])
                if payments_account:
                    for j in payments_account:
                        diary_id = j.name
            vals = {
                'diario': diary_id,
                'debito': rects['debit']
                }
            move_income_ids.append(vals)
        return move_income_ids


    def get_values_to_ecomes(self):
        if self.sd_rango:
            val_ecome = self.env['account.move.line'].search(
                [('name_number', 'like', 'EGR%'), ('journal_id.type', 'in', ('bank', 'cash')), ('credit', '>', 0),
                 ('debit', '=', 0), ('date', '>=', self.start_date), ('date', '<=', self.start_date),
                 ('company_id', '=', 1), ('move_id.state', '=', 'posted'), ('move_id.state', '!=', 'draft'),
                 ('move_id.payment_state', '!=', 'reversed')])
            grouped_ecomes = val_ecome.read_group(
                [('name_number', 'like', 'EGR%'), ('journal_id.type', 'in', ('bank', 'cash')), ('credit', '>', 0),
                 ('debit', '=', 0), ('date', '>=', self.start_date), ('date', '<=', self.start_date),
                 ('company_id', '=', 1), ('move_id.state', '=', 'posted'), ('move_id.state', '!=', 'draft'),
                 ('move_id.payment_state', '!=', 'reversed')], ['account_id', 'credit'], ['account_id', 'credit'])

        else:
            val_ecome = self.env['account.move.line'].search([('name_number','like','EGR%'),('journal_id.type', 'in', ('bank', 'cash')),('credit','>',0),('debit','=',0),('date','=',self.start_date),('company_id', '=', 1),('move_id.state', '=', 'posted'),('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')])
            grouped_ecomes = val_ecome.read_group([('name_number','like','EGR%'),('journal_id.type', 'in', ('bank', 'cash')),('credit','>',0),('debit','=',0), ('date','=',self.start_date),('company_id', '=', 1),('move_id.state', '=', 'posted'), ('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')],  ['account_id', 'credit'], ['account_id', 'credit'])

        move_encome_ids = []
        # self.get_difference_by_date()
        diary_id = ''
        for rects in grouped_ecomes:
            val_account = rects['account_id'][0]
            if val_account:
                payments_account = self.env['account.account'].search([('id', '=', val_account)])
                if payments_account:
                    for j in payments_account:
                        diary_id = j.name
            vals = {
                'diario': diary_id,
                'credito': rects['credit']
                }
            move_encome_ids.append(vals)
        return move_encome_ids

    def get_three_primary_word_income(self, words):
        if words:
            value = words[0:3]
            if value == 'ING':
                return True

    def get_three_primary_word_ecome(self, words):
        if words:
            value = words[0:3]
            if value == 'EGR':
                return True

    def get_difference_by_date(self): 
        date_f = self.start_date
        a_day = date_f - timedelta(days=1)

        # val_income = self.env['account.move.line'].search([('name_number','like','ING%'),('journal_id.type', 'in', ('bank', 'cash')),('debit','>',0),('credit','=',0),('date','in',(a_day, date_f)),('date','in',(a_day, date_f)),('company_id', '=', 1),('move_id.state', '=', 'posted'),('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')])
        

        # grouped_partners = val_income.read_group([('name_number','like','ING%'),('journal_id.type', 'in', ('bank', 'cash')),('debit','>',0),('credit','=',0), ('date','in',(a_day, date_f)),('date','in',(a_day, date_f)),('company_id', '=', 1),('move_id.state', '=', 'posted'), ('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')],  ['account_id', 'debit'], ['account_id', 'debit'])

        # val_ecome = self.env['account.move.line'].search([('name_number','like','EGR%'),('journal_id.type', 'in', ('bank', 'cash')),('credit','>',0),('debit','=',0),('date','in',(a_day, date_f)),('date','in',(a_day, date_f)),('company_id', '=', 1),('move_id.state', '=', 'posted'),('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')])
        
        # grouped_ecomes = val_ecome.read_group([('name_number','like','EGR%'),('journal_id.type', 'in', ('bank', 'cash')),('credit','>',0),('debit','=',0), ('date','in',(a_day, date_f)),('date','in',(a_day, date_f)),('company_id', '=', 1),('move_id.state', '=', 'posted'), ('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')],  ['account_id', 'credit'], ['account_id', 'credit'])
        
        if self.start_date:
            get_real_date = self.start_date
            get_one_day_month = datetime(self.start_date.year, self.start_date.month, 1).date()
            
            val_saldos = self.env['account.move.line'].search([('account_id.user_type_id', '=', 3),('date','<',get_real_date),('company_id', '=', self.company_id.id),('move_id.state', '=', 'posted'),('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')])
            
            # val_saldos_gruop = val_saldos.read_group([('journal_id.type', 'in', ('bank', 'cash')),('date','>=',get_one_day_month),('date','<',get_real_date),('company_id', '=', 1),('move_id.state', '=', 'posted'),('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')],  ['account_id', 'balance'], ['account_id', 'balance'])

            val_saldos_gruop = val_saldos.read_group([('account_id.user_type_id', '=', 3),('date','<',get_real_date),('company_id', '=', self.company_id.id),('move_id.state', '=', 'posted'),('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')],  ['account_id', 'balance'], ['account_id', 'balance'])

            a = 0
            lists = []
            flag = False
            if val_saldos_gruop:
                
                for valor_a in val_saldos_gruop:
                    value = valor_a['account_id'][0]
                    if value :
                        flag = True
                        new_val = float(valor_a['balance'])
                        account_journal = self.env['account.account'].search([('id', '=', value)],limit = 1)
                        if account_journal:
                            diary_id = account_journal.name
                        vals = {
                            'name_journal':diary_id,
                            'sustraction': new_val,
                            'id_diary': valor_a['account_id'][0],
                        }
                        lists.append(vals)
            return lists

            # val_saldos = self.env['account.move.line'].search([('journal_id.type', 'in', ('bank', 'cash')),('date','>=',get_one_day_month),('date','<',get_real_date),('company_id', '=', self.company_id.id),('move_id.state', '=', 'posted'),('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')])

            

            

    
            
            
        # val_saldos = self.env['account.move.line'].search([('name_number','like',('ING%','EGR%','TRA%')),('journal_id.type', 'in', ('bank', 'cash')),('date','in',(a_day, date_f)),('date','in',(a_day, date_f)),('company_id', '=', 1),('move_id.state', '=', 'posted'),('move_id.state', '!=', 'draft'),('move_id.payment_state', '!=', 'reversed')])
        
        

        # a = 0
        # lists = []
        # flag = False
        # if grouped_partners and grouped_ecomes:
        #     if len(grouped_partners) == len(grouped_ecomes):
        #         for valor_a in grouped_partners:
        #             value = valor_a['account_id'][0]
        #             for x in grouped_ecomes:
        #                 val_alt = x['account_id'][0]
        #                 if value == val_alt:
        #                     flag = True
        #                     new_val = float(valor_a['debit']) - float(x['credit'])
        #                     account_journal = self.env['account.account'].search([('id', '=', value)],limit = 1)
        #                     if account_journal:
        #                         diary_id = account_journal.name
        #                     vals = {
        #                         'name_journal':diary_id,
        #                         'sustraction': new_val,
        #                         'id_diary': valor_a['account_id'][0],
        #                         # 'position' : grouped_partners.index(valor_a),
        #                         # 'position_two' : grouped_ecomes.index(x)
        #                     }
        #                     lists.append(vals)
        #         values_incomess = [diccionario['account_id'][0] for diccionario in grouped_partners]
        #         values_ecomess = [diccionario_two['account_id'][0] for diccionario_two in grouped_ecomes]
        #         values_salds = [diccionario_tree['id_diary'] for diccionario_tree in lists]

        #         for hh in grouped_partners:
        #             a = 0
        #             if hh['account_id'][0] not in values_ecomess and hh['account_id'][0] not in values_salds: 
        #                 new_val = float(hh['debit'])
        #                 account_journal = self.env['account.account'].search([('id', '=', hh['account_id'][0])],limit = 1)
        #                 if account_journal:
        #                     diary_id = account_journal.name
        #                 vals = {
        #                         'name_journal':diary_id,
        #                         'sustraction': new_val,
        #                         'id_diary': hh['account_id'][0],
        #                         # 'position' : grouped_partners.index(hh),
        #                         # 'position_two' : grouped_ecomes.index(x)
        #                     }
        #                 lists.append(vals)

        #         for ii in grouped_ecomes:
        #             a = 0
        #             if ii['account_id'][0] not in values_incomess and ii['account_id'][0] not in values_salds: 
        #                 new_val = float(ii['credit'])
        #                 account_journal = self.env['account.account'].search([('id', '=', ii['account_id'][0])],limit = 1)
        #                 if account_journal:
        #                     diary_id = account_journal.name
        #                 vals = {
        #                         'name_journal':diary_id,
        #                         'sustraction': new_val,
        #                         'id_diary': ii['account_id'][0],
        #                         # 'position' : grouped_partners.index(ii),
        #                         # 'position_two' : grouped_ecomes.index(x)
        #                     }
        #                 lists.append(vals)

                    

        #     if len(grouped_partners) > len(grouped_ecomes):
        #         if len(grouped_partners) >= 1:
        #             for y in grouped_partners:
        #                 value = y['account_id'][0]
        #                 cont = len(grouped_ecomes)
        #                 for valor_b in grouped_ecomes: 
        #                     if value == valor_b['account_id'][0]:
        #                         new_val = float(y['debit']) - float(valor_b['credit'])
        #                         account_journal = self.env['account.account'].search([('id', '=', value)],limit = 1)
        #                         if account_journal:
        #                             diary_id_name = account_journal.name
        #                         vals = {
        #                             'name_journal':diary_id_name,
        #                             'sustraction': new_val,
        #                             'id_diary': y['account_id'][0]
        #                         }
        #                         lists.append(vals)
        #                         cont +=1
                        
        #                 if len(grouped_ecomes) == cont:
        #                     account_journal_list = self.env['account.account'].search([('id', '=', value)],limit = 1)
        #                     if account_journal_list:
        #                         diary_id = account_journal_list.name
        #                     vals = {
        #                             'name_journal':diary_id,
        #                             'sustraction': float(y['debit']),
        #                             'id_diary': y['account_id'][0]
        #                             }
        #                     lists.append(vals)
        #         values_incomess = [diccionario['account_id'][0] for diccionario in grouped_partners]
        #         values_ecomess = [diccionario_two['account_id'][0] for diccionario_two in grouped_ecomes]
        #         values_salds = [diccionario_tree['id_diary'] for diccionario_tree in lists]

        #         for hh in grouped_partners:
        #             a = 0
        #             if hh['account_id'][0] not in values_ecomess and hh['account_id'][0] not in values_salds: 
        #                 new_val = float(hh['debit'])
        #                 account_journal = self.env['account.account'].search([('id', '=', hh['account_id'][0])],limit = 1)
        #                 if account_journal:
        #                     diary_id = account_journal.name
        #                 vals = {
        #                         'name_journal':diary_id,
        #                         'sustraction': new_val,
        #                         'id_diary': hh['account_id'][0],
        #                         # 'position' : grouped_partners.index(hh),
        #                         # 'position_two' : grouped_ecomes.index(x)
        #                     }
        #                 lists.append(vals)

        #         for ii in grouped_ecomes:
        #             a = 0
        #             if ii['account_id'][0] not in values_incomess and ii['account_id'][0] not in values_salds: 
        #                 new_val = float(ii['credit'])
        #                 account_journal = self.env['account.account'].search([('id', '=', ii['account_id'][0])],limit = 1)
        #                 if account_journal:
        #                     diary_id = account_journal.name
        #                 vals = {
        #                         'name_journal':diary_id,
        #                         'sustraction': new_val,
        #                         'id_diary': ii['account_id'][0],
        #                         # 'position' : grouped_partners.index(ii),
        #                         # 'position_two' : grouped_ecomes.index(x)
        #                     }
        #                 lists.append(vals)

        #     if len(grouped_ecomes) > len(grouped_partners):
        #         if len(grouped_ecomes) >= 1:
        #             for y in grouped_ecomes:
        #                 value = y['account_id'][0]
        #                 cont = len(grouped_partners)
        #                 for valor_b in grouped_partners: 
        #                     if value == valor_b['account_id'][0]:
        #                         new_val = float(y['debit']) - float(valor_b['credit'])
        #                         account_journal = self.env['account.account'].search([('id', '=', value)],limit = 1)
        #                         if account_journal:
        #                             diary_id_name = account_journal.name
        #                         vals = {
        #                             'name_journal':diary_id_name,
        #                             'sustraction': new_val
        #                         }
        #                         lists.append(vals)
        #                         cont +=1
                        
        #                 if len(grouped_partners) == cont:
        #                     account_journal_list = self.env['account.account'].search([('id', '=', value)],limit = 1)
        #                     if account_journal_list:
        #                         diary_id = account_journal_list.name
        #                     vals = {
        #                             'name_journal':diary_id,
        #                             'sustraction': float(y['debit'])
        #                             }
        #                     lists.append(vals)

        #         values_incomess = [diccionario['account_id'][0] for diccionario in grouped_partners]
        #         values_ecomess = [diccionario_two['account_id'][0] for diccionario_two in grouped_ecomes]
        #         values_salds = [diccionario_tree['id_diary'] for diccionario_tree in lists]

        #         for hh in grouped_partners:
        #             a = 0
        #             if hh['account_id'][0] not in values_ecomess and hh['account_id'][0] not in values_salds: 
        #                 new_val = float(hh['debit'])
        #                 account_journal = self.env['account.account'].search([('id', '=', hh['account_id'][0])],limit = 1)
        #                 if account_journal:
        #                     diary_id = account_journal.name
        #                 vals = {
        #                         'name_journal':diary_id,
        #                         'sustraction': new_val,
        #                         'id_diary': hh['account_id'][0],
        #                         # 'position' : grouped_partners.index(hh),
        #                         # 'position_two' : grouped_ecomes.index(x)
        #                     }
        #                 lists.append(vals)

        #         for ii in grouped_ecomes:
        #             a = 0
        #             if ii['account_id'][0] not in values_incomess and ii['account_id'][0] not in values_salds: 
        #                 new_val = float(ii['credit'])
        #                 account_journal = self.env['account.account'].search([('id', '=', ii['account_id'][0])],limit = 1)
        #                 if account_journal:
        #                     diary_id = account_journal.name
        #                 vals = {
        #                         'name_journal':diary_id,
        #                         'sustraction': new_val,
        #                         'id_diary': ii['account_id'][0],
        #                         # 'position' : grouped_partners.index(ii),
        #                         # 'position_two' : grouped_ecomes.index(x)
        #                     }
        #                 lists.append(vals)
                            
                        
            # if grouped_partners
        # return lists