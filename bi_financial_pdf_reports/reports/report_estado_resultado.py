from odoo import api, models

class EstadoResultadoReport(models.AbstractModel):
    _name = 'report.bi_financial_pdf_reports.sd_report_er'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'accounting.report.bi',
            'data': data,
        }

class EstadoResultadoReport(models.AbstractModel):
    _name = 'report.bi_financial_pdf_reports.sd_report_er_v3'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'accounting.report.bi',
            'data': data,
        }
