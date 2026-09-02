# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
import datetime

from odoo import api, fields, models
import time
from odoo.exceptions import UserError


class AccountFinancialReport(models.Model):
    _name='account.financial.report'

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if name:
            domain = ['|', ('name', operator, name), ('display_name', operator, name)]
            recs = self.search(domain + args, limit=limit)
        else:
            recs = self.search(args, limit=limit)
        return recs.name_get()


    parent_id = fields.Many2one('account.financial.report', string='Padre')
    def _get_children_by_order(self,type_order):
        res = self
        if type_order == 'number':
            #ordenar cuentas para imprimir -Henry
            children = self.search([('parent_id', 'in', self.ids)], order='st_numero_orden ASC')
        elif type_order == 'account_number':
            children = self.search([('parent_id', 'in', self.ids)], order='sd_numero_cuenta ASC')
        else:
            children = self.search([('parent_id', 'in', self.ids)], order='sequence ASC')
        if children:
            for child in children:
                res += child._get_children_by_order(type_order)
        return res
    @api.depends('parent_id', 'parent_id.level')
    def _get_level(self):
        for report in self:
            level = 0
            if report.parent_id:
                level = report.parent_id.level + 1
            report.level = level
    name = fields.Char('Nombre del Informe', translate=True)
    level = fields.Integer(compute='_get_level', string='Nivel', store=True)
    sequence = fields.Integer('Sequence')
    children_ids = fields.One2many('account.financial.report', 'parent_id', 'Informe de Cuenta')
    # aumentar tipo de resultado
    type = fields.Selection([
        ('sum', 'Vista'),
        ('accounts', 'Cuentas'),
        ('account_type', 'Tipo de cuentas'),
        ('account_report', 'Valor del informe'),
        ('result_type', 'Tipo de resultado')], 'Tipo', default='sum')
    account_ids = fields.Many2many('account.account', 'account_account_financial_report', 'report_line_id','account_id', 'Cuentas')
    account_report_id = fields.Many2one('account.financial.report', 'Valor del informe')
    account_type_ids = fields.Many2many('account.account.type', 'account_account_financial_report_type', 'report_id','account_type_id', 'Tipo de Cuentas')
    sign = fields.Selection([('-1', 'Signo de balance inverso'), ('1', 'Preservar signo de balance')], 'Signo del Reporte',
                            required=True, default='1',
                            help='For accounts that are typically more debited than credited and that you would like to print as negative amounts in your reports, you should reverse the sign of the balance; e.g.: Expense account. The same applies for accounts that are typically more credited than debited and that you would like to print as positive amounts in your reports; e.g.: Income account.')
    display_detail = fields.Selection([
        ('no_detail', 'Sin detalle'),
        ('detail_flat', 'Mostrar Hijos Fijos'),
        ('detail_with_hierarchy', 'Mostrar Hijos con Jeraquia')
    ], 'Mostrar detalles', default='detail_flat')
    style_overwrite = fields.Selection([
        ('0', 'Formato Predeterminado'),
        ('1', 'Título principal 1 (negrita, subrayado)'),
        ('2', 'Título 2 (negrita)'),
        ('3', 'Título 3 (negrita, más pequeña)'),
        ('4', 'Texto normal'),
        ('5', 'Texto en cursiva (más pequeño)'),
        ('6', 'Texto más pequeño'),
    ], 'Estilo de informe financiero', default='0',
        help="Puede configurar aquí el formato en el que desea que se muestre este registro. Si deja el formato automático, se calculará en función de la jerarquía de informes financieros (campo 'nivel' calculado automáticamente).")
    # Henry
    st_excluir_diario = fields.Many2many('account.journal', string='Nombre Diario')
    # para Controlar orden
    st_numero_orden = fields.Integer(string='Numero de orden')
    # para filtrar por interno o contable
    sd_tipo_reporte = fields.Selection([
        ('estado_resultado','Padre Estado de Resultado'),
        ('balance_general','Padre Balance General'),
        ('hijos','Hijo'),
    ],string='Reporte', default='hijos', required=True)
    sd_numero_cuenta = fields.Char(string ='Nº Cuenta')
    sd_account_financial_report_line_ids = fields.One2many('account.financial.report.line','sd_report_bi_financial_id')
    sd_planilla = fields.Many2one('ir.actions.report', string='Planilla')
    sd_type_order = fields.Selection([
        ('number','Por Numero'),
        ('account_number','Por Numero de Cuenta'),
    ],string='Tipo de Orden')

    def name_get(self):
        result = []
        for record in self:
            name = record.sd_numero_cuenta or ''
            if name and isinstance(record.name, str):
                name += ' ' + record.name
            elif name:
                name += ' ' + str(record.name)
            elif not name:
                name = record.name or ''
            result.append((record.id, name))
        return result


class AccountingReportBi(models.TransientModel):
    _name = "accounting.report.bi"
    _description = "Accounting Report"
    @api.model
    def _get_account_report(self):
        reports = []
        if self._context.get('active_id'):
            menu = self.env['ir.ui.menu'].browse(self._context.get('active_id')).name
            reports = self.env['account.financial.report'].search([('name', 'ilike', menu)])
        return reports and reports[0] or False
    company_id = fields.Many2one('res.company', string='Company', readonly=True,default=lambda self: self.env.user.company_id)
    journal_ids = fields.Many2many('account.journal', string='Diario', required=False)
    date_from = fields.Date(string='Fecha de inicio')
    date_to = fields.Date(string='Fecha final')
    display_account = fields.Selection([('all', 'Todo'), ('movement', 'Con movimientos'),('not_zero', 'Con saldo no es igual a 0'), ],
                                       string='Mostrar cuentas', required=True, default='movement')
    target_move = fields.Selection([
        ('posted', 'Todas las entradas publicadas'),
        ('all', 'Todas las entradas'),], string='Movimientos de destino', required=True, default='posted')
    enable_filter = fields.Boolean(string='Habilitar comparación')
    account_report_id = fields.Many2one('account.financial.report', string='Account Reports',
                                        default=_get_account_report)
    label_filter = fields.Char(string='Etiqueta de columna',
                               help="This label will be displayed on report to show the balance computed for the given comparison filter.")
    filter_cmp = fields.Selection([('filter_no', 'Sin filtros'), ('filter_date', 'Fecha')], string='Filtrado por',
                                  required=True, default='filter_no')
    date_from_cmp = fields.Date(string='Fecha inicio')
    date_to_cmp = fields.Date(string='Fecha final')
    debit_credit = fields.Boolean(string='Mostrar columnas de débito / crédito',help="This option allows you to get more details about the way your balances are computed. Because it is space consuming, we do not allow to use it while doing a comparison.")
    initial_balance = fields.Boolean(string='Incluir saldos iniciales',default=True,
                                     help='If you selected date, this field allow you to add a row to display the amount of debit/credit/balance that precedes the filter you\'ve set.')
    sortby = fields.Selection([('sort_date', 'Fecha'), ('sort_journal_partner', 'Diario & y Asociado')], string='Ordenar por',required=True, default='sort_date')
    # Henry
    sd_account_id = fields.Many2many('account.account', string='Cuenta')
    currency_id = fields.Many2one('res.currency', string='Moneda')
    sd_tipo_reporte_libro_mayor = fields.Selection([('action_report_general_ledger','Clasico'), ('action_report_general_ledger_v2','Minimalista')], string='Tipo de Reporte', default='action_report_general_ledger_v2')
    # Filtrar por Interno o contable
    @api.model
    def _tipo_estado_resultado(self):
        reportes = self.env['account.financial.report'].search([('sd_tipo_reporte','=','estado_resultado')])
        if reportes:
            return reportes.mapped('id')
        else:
            return []

    @api.model
    def _tipo_balance_general(self):
        reportes = self.env['account.financial.report'].search([('sd_tipo_reporte','=','balance_general')])
        if reportes:
            return reportes.mapped('id')
        else:
            return []

    @api.model
    def _get_default_estado_resultado(self):
        return self.env['account.financial.report'].search([('sd_tipo_reporte','=','estado_resultado')])

    @api.model
    def _get_default_balance_general(self):
        return self.env['account.financial.report'].search([('sd_tipo_reporte','=','balance_general')])

    sd_estado_resulado = fields.Many2one('account.financial.report',domain=lambda self: [('id', 'in', self._tipo_estado_resultado())],
                                         default=_get_default_estado_resultado)
    sd_balance_general = fields.Many2one('account.financial.report',domain=lambda self: [('id', 'in', self._tipo_balance_general())],
                                         default=_get_default_balance_general)

    # ESI: opciones de desglose para los reportes financieros.
    esi_con_analitica = fields.Boolean(string='Mostrar cuentas analíticas')
    esi_partner = fields.Boolean(string='Desglosar cuentas por cobrar/pagar por contacto')
    esi_analytic_account_ids = fields.Many2many('account.analytic.account', string='Analítica')
    esi_partner_ids = fields.Many2many('res.partner', string='Empresa')
    esi_cash_flow_ids = fields.Many2many('esi.cash.flow', string='Cuentas de Flujo')

    def _esi_trial_extra_sql(self, table='account_move_line'):
        """Filtros de Sumas y Saldos a nivel de asiento para conservar partida doble.

        Si una analítica, empresa o CTA Flujo aparece en cualquier línea del asiento,
        se incluyen todas las líneas del asiento. Así Débito y Crédito siguen cuadrando.
        """
        if not self.env.context.get('esi_trial_filters'):
            return '', []
        sql, params = '', []
        if self.esi_analytic_account_ids:
            sql += (' AND EXISTS (SELECT 1 FROM account_move_line esi_af '
                    'WHERE esi_af.move_id = %s.move_id AND esi_af.analytic_account_id IN %%s)' % table)
            params.append(tuple(self.esi_analytic_account_ids.ids))
        if self.esi_partner_ids:
            sql += (' AND EXISTS (SELECT 1 FROM account_move_line esi_pf '
                    'WHERE esi_pf.move_id = %s.move_id AND esi_pf.partner_id IN %%s)' % table)
            params.append(tuple(self.esi_partner_ids.ids))
        if self.esi_cash_flow_ids:
            sql += (' AND EXISTS (SELECT 1 FROM account_move_line esi_cf '
                    'WHERE esi_cf.move_id = %s.move_id AND esi_cf.esi_cash_flow_id IN %%s)' % table)
            params.append(tuple(self.esi_cash_flow_ids.ids))
        return sql, params

    def _esi_compute_breakdown(self, accounts, group_field, diarios=None):
        """Agrupa movimientos por cuenta y por analítica/contacto respetando el contexto contable."""
        result = {}
        if not accounts:
            return result
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"', '') if tables else 'account_move_line'
        filters = ''
        params = [tuple(accounts.ids)]
        if where_clause.strip():
            filters += ' AND ' + where_clause.strip()
            params += list(where_params)
        if diarios:
            filters += ' AND account_move_line.journal_id IN %s'
            params.append(tuple(diarios.ids))
        extra_sql, extra_params = self._esi_trial_extra_sql('account_move_line')
        filters += extra_sql
        params += extra_params
        query = (
            "SELECT account_id, %s AS group_id, "
            "COALESCE(SUM(debit),0) AS debit, COALESCE(SUM(credit),0) AS credit, "
            "COALESCE(SUM(debit),0) - COALESCE(SUM(credit),0) AS balance "
            "FROM %s WHERE account_id IN %%s%s GROUP BY account_id, %s"
        ) % (group_field, tables, filters, group_field)
        self.env.cr.execute(query, tuple(params))
        for row in self.env.cr.dictfetchall():
            result.setdefault(row['account_id'], []).append(row)
        return result

    def _esi_breakdown_lines(self, account, sign, analytic_rows=None, partner_rows=None,
                             analytic_cmp=None, partner_cmp=None):
        """Construye líneas informativas debajo de una cuenta sin alterar su total."""
        result = []
        rate = self.currency_id.rate or 1
        currency = account.company_id.currency_id

        def add_rows(rows, cmp_map, model, kind):
            rows = list(rows or [])
            existing_groups = {row.get('group_id') for row in rows}
            for group_id, cmp_balance in (cmp_map or {}).items():
                if group_id not in existing_groups:
                    rows.append({'group_id': group_id, 'debit': 0.0, 'credit': 0.0,
                                 'balance': 0.0, 'comp_balance': cmp_balance})
            for row in rows:
                debit = row.get('debit') or 0.0
                credit = row.get('credit') or 0.0
                balance = row.get('balance') or 0.0
                comp_balance = (cmp_map or {}).get(row.get('group_id'), row.get('comp_balance', 0.0))
                if (currency.is_zero(debit) and currency.is_zero(credit)
                        and currency.is_zero(balance) and currency.is_zero(comp_balance)):
                    continue
                # No se muestra ningún desglose cuando la línea no tiene analítica/contacto.
                if not row.get('group_id'):
                    continue
                rec = self.env[model].browse(row.get('group_id'))
                if not rec.exists():
                    continue
                name = rec.name
                vals = {
                    'number_cuenta': '', 'name': name,
                    'balance': balance * int(sign) * rate,
                    'type': kind, 'level': 6,
                    'account_type': account.internal_type,
                    'esi_detail': True,
                }
                if self.debit_credit:
                    vals.update({'debit': debit, 'credit': credit})
                if self.enable_filter:
                    vals['balance_cmp'] = comp_balance * int(sign) * rate
                result.append(vals)

        if self.esi_con_analitica:
            add_rows(analytic_rows, analytic_cmp, 'account.analytic.account', 'analytic')
        if self.esi_partner and account.internal_type in ('receivable', 'payable'):
            add_rows(partner_rows, partner_cmp, 'res.partner', 'partner')
        return result

    def _compute_account_balance(self, accounts,diarios):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }
        # encluir diarios id
        ids_diario = diarios.mapped('id')
        res = {}
        for account in accounts:
            res[account.id] = dict.fromkeys(mapping, 0.0)
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE account_id IN %s " \
                      + filters +"and account_move_line.journal_id IN %s "+ \
                      " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params) + (tuple(ids_diario),)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        # print('res',res)
        return res

    def _compute_report_balance(self, reports):
        res = {}
        fields = ['credit', 'debit', 'balance']
        #ordenar cuentas para la Impresion - Henry
        reports = sorted(reports,key=lambda reporte : int(str(reporte.level + reporte.st_numero_orden)))
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                res[report.id]['account'] = self._compute_account_balance(report.account_ids, report.st_excluir_diario or self.env['account.journal'].search([]))
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts, report.st_excluir_diario or self.env['account.journal'].search([]))
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            #CODIGO HENRY
            elif report.type == 'result_type':
                for report_line_id in report.sd_account_financial_report_line_ids:
                    res2 = self._compute_report_balance(report_line_id.sd_report_id)
                    for key, value in res2.items():
                        for field in fields:
                            res[report.id][field] = res[report.id][field] + (value[field] * int(report_line_id.sd_operacion_report or 1) if value[field]!=0 else value[field])

        return res

    def get_account_lines(self):
        lines = []
        child_reports = self.account_report_id._get_children_by_order(self.account_report_id.sd_type_order)


        used_context_dict = {
            'state': self.target_move,
            'date_from': self.date_from or self._get_first_move_line_date(),
            'date_to': self.date_to,
            'journal_ids': [a.id for a in self.journal_ids],
            'strict_range': True
        }
        res = self.with_context(used_context_dict)._compute_report_balance(child_reports)
        if self.enable_filter:
            comparison_context_dict = {
                'journal_ids': [a.id for a in self.journal_ids],
                'state': self.target_move,
            }
            if self.filter_cmp == 'filter_date':
                comparison_context_dict.update({"date_to": self.date_to_cmp,
                                                "date_from": self.date_from_cmp})
            comparison_res = self.with_context(comparison_context_dict)._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']
        for report in child_reports:
            vals = {
                'number_cuenta':report.sd_numero_cuenta,
                'name': report.name,
                'balance': (res[report.id]['balance'] * int(report.sign)) * (self.currency_id.rate or 1),
                'type': 'report',
                'level': bool(report.style_overwrite) and int(report.style_overwrite) or report.level,
                'account_type': report.type or False,  # used to underline the financial report balances
            }
            if self.debit_credit:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if self.enable_filter:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * int(report.sign)

            lines.append(vals)
            if report.display_detail == 'no_detail':
                continue

            if res[report.id].get('account'):
                sub_lines = []
                report_accounts = self.env['account.account'].browse(list(res[report.id]['account'].keys()))
                diarios = report.st_excluir_diario or self.env['account.journal'].search([])
                analytic_breakdown = {}
                partner_breakdown = {}
                analytic_cmp_breakdown = {}
                partner_cmp_breakdown = {}
                if self.esi_con_analitica:
                    analytic_breakdown = self.with_context(used_context_dict)._esi_compute_breakdown(
                        report_accounts, 'analytic_account_id', diarios)
                if self.esi_partner:
                    partner_breakdown = self.with_context(used_context_dict)._esi_compute_breakdown(
                        report_accounts.filtered(lambda a: a.internal_type in ('receivable', 'payable')),
                        'partner_id', diarios)
                if self.enable_filter:
                    if self.esi_con_analitica:
                        analytic_cmp_rows = self.with_context(comparison_context_dict)._esi_compute_breakdown(
                            report_accounts, 'analytic_account_id', diarios)
                        analytic_cmp_breakdown = {
                            account_id: {r.get('group_id'): r.get('balance', 0.0) for r in rows}
                            for account_id, rows in analytic_cmp_rows.items()
                        }
                    if self.esi_partner:
                        partner_cmp_rows = self.with_context(comparison_context_dict)._esi_compute_breakdown(
                            report_accounts.filtered(lambda a: a.internal_type in ('receivable', 'payable')),
                            'partner_id', diarios)
                        partner_cmp_breakdown = {
                            account_id: {r.get('group_id'): r.get('balance', 0.0) for r in rows}
                            for account_id, rows in partner_cmp_rows.items()
                        }
                account_items = sorted(
                    res[report.id]['account'].items(),
                    key=lambda item: self.env['account.account'].browse(item[0]).code or '')
                for account_id, value in account_items:
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'number_cuenta': account.code,
                        'name': account.name,
                        'balance': (value['balance'] * int(report.sign) or 0.0) * (self.currency_id.rate or 1),
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and 5,
                        'account_type': account.internal_type,
                    }
                    if self.debit_credit:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(
                                vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance']):
                        flag = True
                    if self.enable_filter:
                        vals['balance_cmp'] = value['comp_bal'] * int(report.sign)
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                        sub_lines += self._esi_breakdown_lines(
                            account, report.sign,
                            analytic_breakdown.get(account_id), partner_breakdown.get(account_id),
                            analytic_cmp_breakdown.get(account_id), partner_cmp_breakdown.get(account_id))
                lines += sub_lines
        return lines

    # Antigua funcion para imprimir Balance General
    def check_report(self):
        self.account_report_id = self.sd_balance_general
        if not self.account_report_id:
            raise UserError('El campo "Tipo" es Obligatorio.\n Porfavor Rellene el campo.')
        final_dict = {}
        # arreglar error fecha Henry
        if not self.date_to:
            self.write({
                'date_to': fields.Datetime.now()
            })
        if self.enable_filter:
            self.debit_credit = False
        if self.enable_filter and self.filter_cmp == 'filter_date':
            if self.date_to_cmp <= self.date_from_cmp:
                raise UserError('Comparison end date should be greater then to Comparison start date.')
        report_lines = self.get_account_lines()
        linea_add = self.return_linea_add_report(len(report_lines)-1)
        final_dict.update({'report_lines': report_lines,
                           'name': self.account_report_id.name,
                           'debit_credit': self.debit_credit,
                           'enable_filter': self.enable_filter,
                           'label_filter': self.label_filter,
                           'target_move': self.target_move,
                           'date_from': self.date_from,
                           'date_to': self.date_to,
                           'company_name': self.company_id.name,
                           'nit': self.company_id.vat,
                           'linea_add': linea_add,
                           'currency':self.currency_id.currency_unit_label or self.env.company.currency_id.currency_unit_label,
                           })

        # return self.env.ref('bi_financial_pdf_reports.action_report_balancesheet').report_action(self, data=final_dict)
        # print('final dict: ', final_dict)
        return self.sd_balance_general.sd_planilla.report_action(self, data=final_dict)
    def _get_first_move_line_date(self):
        # Método para obtener la fecha del primer registro de account.move.line
        first_move_line = self.env['account.move.line'].search([], order='date', limit=1)
        return first_move_line.date if first_move_line else fields.Date.today()

    def return_linea_add_report(self,lineas):
        if lineas <= 45:
            if lineas == 45:
                return 0
            else:
                add_linea = 45 - lineas
                return add_linea
        else:
            add_linea = 45 - (lineas % 45)
            return add_linea
    def check_report_estado_resultado(self):
        self.account_report_id = self.sd_estado_resulado
        if not self.account_report_id:
            raise UserError('El campo "Tipo" es Obligatorio.\n Porfavor Rellene el campo.')
        final_dict = {}
        # arreglar error fecha Henry
        if not self.date_to:
            self.write({
                'date_to': fields.Datetime.now()
            })
        if self.enable_filter:
            self.debit_credit = False
        if self.enable_filter and self.filter_cmp == 'filter_date':
            if self.date_to_cmp <= self.date_from_cmp:
                raise UserError('Comparison end date should be greater then to Comparison start date.')
        report_lines = self.get_account_lines()
        linea_add = self.return_linea_add_report(len(report_lines) - 1)
        self.switch_demo('division')
        final_dict.update({'report_lines': report_lines,
                           'name': self.account_report_id.name,
                           'debit_credit': self.debit_credit,
                           'enable_filter': self.enable_filter,
                           'label_filter': self.label_filter,
                           'target_move': self.target_move,
                           'date_from': self.date_from,
                           'date_to': self.date_to,
                           'company_name': self.company_id.name,
                           'nit': self.company_id.vat,
                           'linea_add': linea_add,
                           'currency': self.currency_id.currency_unit_label or self.env.company.currency_id.currency_unit_label,
                           })
        # return self.env.ref('bi_financial_pdf_reports.action_report_estado_resultado').report_action(self, data=final_dict)
        return self.sd_estado_resulado.sd_planilla.report_action(self,data=final_dict)
    def switch_demo(self,argument):
        switcher = {
            'suma': 4+5,
            'mmultiplicacion': 4*5,
            'division': 4/5,
            'resta': 4-5,

        }
        print(switcher.get(argument, "Argumento invalido"))
    def _get_accounts(self, accounts, display_account):

        account_result = {}
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"', '')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        extra_sql, extra_params = self._esi_trial_extra_sql('account_move_line')
        filters += extra_sql
        request = (
                    "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                    " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params) + tuple(extra_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        analytic_breakdown = self._esi_compute_breakdown(accounts, 'analytic_account_id') if self.esi_con_analitica else {}
        partner_accounts = accounts.filtered(lambda a: a.internal_type in ('receivable', 'payable'))
        partner_breakdown = self._esi_compute_breakdown(partner_accounts, 'partner_id') if self.esi_partner else {}

        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result:
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            include = display_account == 'all'
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                include = True
            if display_account == 'movement' and (
                    not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
                include = True
            if include:
                account_res.append(res)
                if self.esi_con_analitica:
                    for row in analytic_breakdown.get(account.id, []):
                        if not row.get('group_id'):
                            continue
                        rec = self.env['account.analytic.account'].browse(row.get('group_id'))
                        if not rec.exists():
                            continue
                        account_res.append({
                            'code': '',
                            'name': rec.name,
                            'debit': row.get('debit') or 0.0,
                            'credit': row.get('credit') or 0.0,
                            'balance': row.get('balance') or 0.0,
                            'esi_detail': True,
                            'esi_detail_type': 'analytic',
                        })
                if self.esi_partner and account.internal_type in ('receivable', 'payable'):
                    for row in partner_breakdown.get(account.id, []):
                        if not row.get('group_id'):
                            continue
                        rec = self.env['res.partner'].browse(row.get('group_id'))
                        if not rec.exists():
                            continue
                        account_res.append({
                            'code': '',
                            'name': rec.name,
                            'debit': row.get('debit') or 0.0,
                            'credit': row.get('credit') or 0.0,
                            'balance': row.get('balance') or 0.0,
                            'esi_detail': True,
                            'esi_detail_type': 'partner',
                        })
        return account_res

    def print_trial_balance(self):
        if self.date_to or self.date_from:
            if self.date_to <= self.date_from:
                raise UserError('End date should be greater then to start date.')
        display_account = self.display_account
        accounts = self.sd_account_id if self.sd_account_id else self.env['account.account'].search([])
        used_context_dict = {
            'state': self.target_move,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'journal_ids': False,
            'strict_range': True,
            'esi_trial_filters': True
        }
        account_res = self.with_context(used_context_dict)._get_accounts(accounts, display_account)
        final_dict = {}
        final_dict.update({'account_res': account_res,
                           'display_account': self.display_account,
                           'target_move': self.target_move,
                           'date_from': self.date_from,
                           'date_to': self.date_to,
                           'account_names': ', '.join(self.sd_account_id.mapped('display_name')),
                           'analytic_names': ', '.join(self.esi_analytic_account_ids.mapped('display_name')),
                           'partner_names': ', '.join(self.esi_partner_ids.mapped('display_name')),
                           'cash_flow_names': ', '.join(self.esi_cash_flow_ids.mapped('display_name')),
                           })
        return self.env.ref('bi_financial_pdf_reports.action_report_trial_balance').report_action(self, data=final_dict)

    def _get_account_move_entry(self, accounts, init_balance, sortby, display_account, Cuentas):
        # Obtiene las líneas del Libro Mayor y, opcionalmente, su cuenta analítica.
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}
        analytic_ids = self.esi_analytic_account_ids.ids

        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(
                date_from=self.env.context.get('date_from'), date_to=False, initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            analytic_filter = ''
            analytic_params = ()
            if analytic_ids:
                analytic_filter = ' AND l.analytic_account_id IN %s '
                analytic_params = (tuple(analytic_ids),)

            sql = ("SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, "
                   "0.0 AS amount_currency, '' AS lref, 'Initial Balance' AS lname, "
                   "COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, "
                   "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance, "
                   "'' AS lpartner_id, '' AS move_name, '' AS mmove_id, '' AS currency_code, "
                   "NULL AS currency_id, '' AS invoice_id, '' AS invoice_type, '' AS invoice_number, "
                   "'' AS partner_name, '' AS analytic_name "
                   "FROM account_move_line l "
                   "LEFT JOIN account_move m ON (l.move_id=m.id) "
                   "LEFT JOIN res_currency c ON (l.currency_id=c.id) "
                   "LEFT JOIN res_partner p ON (l.partner_id=p.id) "
                   "JOIN account_journal j ON (l.journal_id=j.id) "
                   "WHERE l.account_id IN %s" + filters + " AND l.account_id IN %s " + analytic_filter +
                   " GROUP BY l.account_id")
            params = (tuple(accounts.ids),) + tuple(init_where_params) + (tuple(Cuentas),) + analytic_params
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
        analytic_filter = ''
        analytic_params = ()
        if analytic_ids:
            analytic_filter = ' AND l.analytic_account_id IN %s '
            analytic_params = (tuple(analytic_ids),)

        sql = ("SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, "
               "j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, "
               "COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, "
               "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance, "
               "m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name, "
               "COALESCE(aa.name, '') AS analytic_name "
               "FROM account_move_line l "
               "JOIN account_move m ON (l.move_id=m.id) "
               "LEFT JOIN res_currency c ON (l.currency_id=c.id) "
               "LEFT JOIN res_partner p ON (l.partner_id=p.id) "
               "LEFT JOIN account_analytic_account aa ON (l.analytic_account_id=aa.id) "
               "JOIN account_journal j ON (l.journal_id=j.id) "
               "JOIN account_account acc ON (l.account_id = acc.id) "
               "WHERE l.account_id IN %s " + filters + " AND l.account_id IN %s " + analytic_filter +
               " GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, "
               "l.ref, l.name, m.name, c.symbol, p.name, aa.name ORDER BY " + sql_sort)

        params = (tuple(accounts.ids),) + tuple(where_params) + (tuple(Cuentas),) + analytic_params
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)

        return account_res


    def print_general_ledger(self):
        if self.date_to or self.date_from:
            if self.date_to <= self.date_from:
                raise UserError('End date should be greater then to start date.')
        init_balance = self.initial_balance
        sortby = self.sortby
        display_account = self.display_account
        codes = []
        #DAVID
        journal_ids = self.env['account.journal'].search([])
        if self.journal_ids and len(self.journal_ids) > 0:
            codes = [journal.code for journal in
                     self.env['account.journal'].search([('id', 'in', self.journal_ids.ids)])]
        else:
            codes = [journal.code for journal in
                     self.env['account.journal'].search([('id', 'in', journal_ids.ids)])]
        #HENRY
        # Cuentas
        id_cuentas = self.sd_account_id.mapped('id')
        if not self.sd_account_id:
            id_cuentas = self.env['account.account'].search([]).mapped('id')
        #Multi Compañia, LA solucion es obtener todas las CUENTAS por sql y no por search
        # id_compañias = self.sd_company_id if self.sd_company_id else self.env['res.company'].search([])

        used_context_dict = {
            'state': self.target_move,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'journal_ids': [a.id for a in self.journal_ids or journal_ids],
            'strict_range': True
        }
        accounts = self.env['account.account'].search([])
        accounts_res = self.with_context(used_context_dict)._get_account_move_entry(accounts, init_balance, sortby,
                                                                                    display_account,id_cuentas)
        final_dict = {}
        final_dict.update(
            {
                'time': time,
                'Account': accounts_res,
                'print_journal': codes,
                'display_account': display_account,
                'target_move': self.target_move,
                'sortby': sortby,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'esi_con_analitica': self.esi_con_analitica
            }
        )
        return self.env.ref('bi_financial_pdf_reports.' + self.sd_tipo_reporte_libro_mayor).report_action(self,data=final_dict)

    def get_current_date(self):
        return (datetime.date.day + '/' + datetime.date.month + '/' + datetime.date.year)


    # -------------------------------------------------------------------------
    # ESI: VISTA PREVIA HTML
    # -------------------------------------------------------------------------
    def action_view_balance_sheet(self):
        self.ensure_one()
        return self.env['esi.financial.report.preview'].open_from_report_action(
            self,
            'Balance General',
            'check_report',
            excel_method='check_report',
            excel_uses_report_type=True,
        )

    def action_view_profit_loss(self):
        self.ensure_one()
        return self.env['esi.financial.report.preview'].open_from_report_action(
            self,
            'Estado de Resultado',
            'check_report_estado_resultado',
            excel_method='check_report_estado_resultado',
            excel_uses_report_type=True,
        )

    def action_view_trial_balance(self):
        self.ensure_one()
        return self.env['esi.financial.report.preview'].open_from_report_action(
            self,
            'Sumas y Saldos',
            'print_trial_balance',
            excel_method='print_trial_balance',
            excel_uses_report_type=True,
        )

    def action_view_general_ledger(self):
        self.ensure_one()
        return self.env['esi.financial.report.preview'].open_from_report_action(
            self,
            'Libro Mayor',
            'print_general_ledger',
            excel_method='print_general_ledger',
            excel_uses_report_type=True,
        )
