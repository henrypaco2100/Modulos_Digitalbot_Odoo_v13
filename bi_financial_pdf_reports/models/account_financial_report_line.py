from odoo import api, fields, models


class AccountFinancialReportLine(models.Model):
    _name = 'account.financial.report.line'
    name = fields.Char(String="Nombre")
    @api.model
    def _filtered_report_type(self):
        # return {'warning': {
        #     'title': 'Advertencia!!',
        #     'message': 'No puede cambiar la ubicación destino cuando existe el tipo de operación'
        # }}
        reportes = self.env['account.financial.report'].search([('type','in',['accounts','account_type','result_type'])])
        if reportes:
            return reportes.mapped('id')
        else:
            return []
    sd_operacion_report = fields.Selection([('1','Suma'),('-1','Resta'),],string='Operacion',default='sumar')
    sd_report_id = fields.Many2one('account.financial.report',string=' Reportes',domain=lambda self: [('id', 'in', self._filtered_report_type())])
    sd_report_bi_financial_id = fields.Many2one('account.financial.report', 'tipos de cuentas operacion',
                                      index=True,  readonly=True, auto_join=True, ondelete="cascade")