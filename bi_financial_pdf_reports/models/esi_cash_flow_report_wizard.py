# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EsiCashFlowReportWizard(models.TransientModel):
    _name = 'esi.cash.flow.report.wizard'
    _description = 'Wizard Reporte Flujo de Caja ESI'

    date_from = fields.Date(string='Desde', required=True, default=lambda self: date.today().replace(day=1))
    date_to = fields.Date(string='Hasta', required=True, default=fields.Date.context_today)
    cash_flow_ids = fields.Many2many('esi.cash.flow', string='Cuentas de Flujo')
    flow_type = fields.Selection([('income', 'Ingreso'), ('expense', 'Egreso')], string='Tipo de flujo')
    analytic_account_ids = fields.Many2many('account.analytic.account', string='Analítica')
    partner_ids = fields.Many2many('res.partner', string='Empresa')
    journal_ids = fields.Many2many('account.journal', string='Diarios')
    company_id = fields.Many2one('res.company', string='Compañía', required=True,
                                 default=lambda self: self.env.user.company_id)
    include_unclassified = fields.Boolean(string='Incluir movimientos sin CTA Flujo', default=False)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError('La fecha Desde no puede ser mayor que la fecha Hasta.')

    def _get_liquidity_lines(self):
        self.ensure_one()
        domain = [('move_id.state', '=', 'posted'), ('company_id', '=', self.company_id.id),
                  ('date', '>=', self.date_from), ('date', '<=', self.date_to),
                  ('account_id.user_type_id.type', '=', 'liquidity')]
        if self.cash_flow_ids:
            domain.append(('esi_cash_flow_id', 'in', self.cash_flow_ids.ids))
        elif not self.include_unclassified:
            domain.append(('esi_cash_flow_id', '!=', False))
        if self.flow_type:
            domain.append(('esi_cash_flow_id.flow_type', '=', self.flow_type))
        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))
        lines = self.env['account.move.line'].search(domain, order='date, move_id, id')

        if self.analytic_account_ids:
            ids = set(self.analytic_account_ids.ids)
            lines = lines.filtered(lambda l: l.analytic_account_id.id in ids or any(
                x.analytic_account_id.id in ids for x in l.move_id.line_ids))
        if self.partner_ids:
            ids = set(self.partner_ids.ids)
            lines = lines.filtered(lambda l: l.partner_id.id in ids or any(
                x.partner_id.id in ids for x in l.move_id.line_ids))
        return lines

    def _prepare_report_data(self):
        self.ensure_one()
        rows, total_income, total_expense = [], 0.0, 0.0
        for line in self._get_liquidity_lines():
            flow = line.esi_cash_flow_id
            income, expense = line.debit or 0.0, line.credit or 0.0
            total_income += income; total_expense += expense
            counterparts = line.move_id.line_ids.filtered(lambda x: x.id != line.id)
            analytic_names = list(dict.fromkeys(counterparts.filtered('analytic_account_id').mapped('analytic_account_id.name')))
            partner_names = list(dict.fromkeys(counterparts.filtered('partner_id').mapped('partner_id.display_name')))
            rows.append({
                'date': line.date, 'move_name': line.move_id.name or '/',
                'journal': line.journal_id.display_name, 'account': line.account_id.display_name,
                'flow': flow.display_name if flow else 'SIN CLASIFICAR',
                'flow_type': flow.flow_type if flow else False,
                'analytic': line.analytic_account_id.display_name or ', '.join(analytic_names),
                'partner': line.partner_id.display_name or ', '.join(partner_names),
                'label': line.name or '', 'income': income, 'expense': expense,
                'net': income - expense,
            })
        return {'rows': rows, 'total_income': total_income, 'total_expense': total_expense,
                'total_net': total_income - total_expense}

    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref('bi_financial_pdf_reports.action_report_esi_cash_flow').report_action(self)

    # ESI: vista previa HTML usando el mismo QWeb del PDF.
    def action_view_report(self):
        self.ensure_one()
        return self.env['esi.financial.report.preview'].open_from_report_action(
            self,
            'Flujo de Caja',
            'action_print_pdf',
            excel_method='action_print_excel',
            excel_uses_report_type=False,
        )
