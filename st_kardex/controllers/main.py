# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request, content_disposition


class KardexDownloadController(http.Controller):

    def _get_report(self, report_id):
        report = request.env['kardex.report'].browse(report_id).exists()
        if not report:
            return False
        report.check_access_rights('read')
        report.check_access_rule('read')
        # Evita descargar un wizard generado por otro usuario, salvo administradores.
        if report.create_uid != request.env.user and not request.env.user.has_group('base.group_system'):
            return False
        return report

    @http.route('/st_kardex/excel/<int:report_id>', type='http', auth='user', methods=['GET'])
    def download_excel(self, report_id, **kwargs):
        report = self._get_report(report_id)
        if not report:
            return request.not_found()
        content, filename = report._build_excel_content()
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(filename)),
            ('Content-Length', str(len(content))),
        ]
        return request.make_response(content, headers=headers)

    @http.route('/st_kardex/pdf/<int:report_id>', type='http', auth='user', methods=['GET'])
    def download_pdf(self, report_id, **kwargs):
        report = self._get_report(report_id)
        if not report:
            return request.not_found()

        action = request.env.ref('st_kardex.kardex_product_report_pdf')
        render_method = getattr(action, '_render_qweb_pdf', None)
        if render_method:
            pdf_content, _content_type = render_method([report.id])
        else:
            pdf_content, _content_type = action.render_qweb_pdf([report.id])

        filename = 'Reporte_Kardex.pdf'
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', content_disposition(filename)),
            ('Content-Length', str(len(pdf_content))),
        ]
        return request.make_response(pdf_content, headers=headers)
