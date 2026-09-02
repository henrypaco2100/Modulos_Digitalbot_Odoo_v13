# -*- coding: utf-8 -*-
# ESI: Vista previa HTML de reportes financieros antes de descargar PDF/Excel.

from lxml import html as lxml_html, etree

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EsiFinancialReportPreview(models.TransientModel):
    _name = 'esi.financial.report.preview'
    _description = 'Vista previa de reporte financiero ESI'

    name = fields.Char(string='Reporte', readonly=True)
    html_content = fields.Html(string='Vista previa', readonly=True, sanitize=False)
    source_model = fields.Char(string='Modelo origen', readonly=True)
    source_id = fields.Integer(string='Registro origen', readonly=True)
    pdf_method = fields.Char(string='Método PDF', readonly=True)
    excel_method = fields.Char(string='Método Excel', readonly=True)
    excel_uses_report_type = fields.Boolean(string='Excel usa contexto report_type', readonly=True)
    excel_available = fields.Boolean(string='Excel disponible', compute='_compute_excel_available')

    @api.depends('source_model', 'source_id', 'excel_method')
    def _compute_excel_available(self):
        """No obliga al módulo PDF a depender del módulo Excel."""
        excel_module = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'bi_financial_excel_reports'),
            ('state', '=', 'installed'),
        ], limit=1)
        installed = bool(excel_module)
        for rec in self:
            source = rec._get_source(silent=True)
            rec.excel_available = bool(
                installed and source and rec.excel_method and hasattr(source, rec.excel_method)
            )

    def _get_source(self, silent=False):
        self.ensure_one()
        if not self.source_model or not self.source_id:
            if silent:
                return False
            raise UserError(_('No se encontró el reporte origen. Vuelva a generar la vista previa.'))
        try:
            source = self.env[self.source_model].browse(self.source_id)
        except KeyError:
            source = False
        if not source or not source.exists():
            if silent:
                return False
            raise UserError(_('La vista previa venció. Vuelva al asistente y pulse "Ver" nuevamente.'))
        return source

    @api.model
    def _extract_body(self, rendered_html):
        """Extrae el contenido visible del QWeb para mostrarlo dentro del backend de Odoo.

        El HTML del reporte contiene su propio <html>/<body>. Insertarlo completo dentro de un
        widget HTML produce estructuras anidadas inválidas. Conservamos el contenido de <main>
        o <body> para que las mismas tablas QWeb puedan verse en la pantalla de Odoo.
        """
        if isinstance(rendered_html, bytes):
            rendered_html = rendered_html.decode('utf-8', errors='replace')
        if not rendered_html:
            return '<div class="alert alert-warning">%s</div>' % _('El reporte no contiene datos para mostrar.')

        try:
            root = lxml_html.fromstring(rendered_html)
            nodes = root.xpath('//main')
            container = nodes[0] if nodes else (root.xpath('//body')[0] if root.xpath('//body') else root)
            content = ''.join(
                etree.tostring(child, encoding='unicode', method='html')
                for child in container.getchildren()
            )
            if not content:
                content = etree.tostring(container, encoding='unicode', method='html')
        except Exception:
            content = rendered_html

        # El contenedor da una apariencia similar a los reportes HTML de MIS y permite tablas anchas.
        return (
            '<div class="esi_financial_report_preview" '
            'style="background:#fff; padding:20px; min-height:500px; overflow-x:auto;">%s</div>'
        ) % content

    @api.model
    def open_from_report_action(self, source, title, pdf_method, excel_method=None,
                                excel_uses_report_type=True):
        """Crea una vista previa usando exactamente el mismo QWeb y los mismos datos del PDF."""
        source.ensure_one()
        pdf_source = source.with_context(esi_html_preview=True, discard_logo_check=True)
        method = getattr(pdf_source, pdf_method, None)
        if not method:
            raise UserError(_('No existe el método de impresión PDF configurado para este reporte.'))

        action = method()
        if not isinstance(action, dict) or action.get('type') != 'ir.actions.report':
            raise UserError(_('No fue posible obtener el reporte para la vista previa.'))

        report_name = action.get('report_name')
        report = self.env['ir.actions.report']._get_report_from_name(report_name)
        if not report:
            raise UserError(_('No se encontró la acción QWeb del reporte: %s') % (report_name or ''))

        action_context = action.get('context') if isinstance(action.get('context'), dict) else {}
        render_context = dict(source.env.context)
        render_context.update(action_context)
        render_context['esi_html_preview'] = True
        html, _output_type = report.with_context(render_context).render_qweb_html(
            source.ids, data=action.get('data')
        )

        preview = self.create({
            'name': title,
            'html_content': self._extract_body(html),
            'source_model': source._name,
            'source_id': source.id,
            'pdf_method': pdf_method,
            'excel_method': excel_method or pdf_method,
            'excel_uses_report_type': excel_uses_report_type,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': title,
            'res_model': 'esi.financial.report.preview',
            'view_mode': 'form',
            'res_id': preview.id,
            'target': 'current',
        }

    def action_print_pdf(self):
        self.ensure_one()
        source = self._get_source()
        method = getattr(source.with_context(esi_html_preview=False), self.pdf_method, None)
        if not method:
            raise UserError(_('No existe el método PDF del reporte.'))
        return method()

    def action_print_excel(self):
        self.ensure_one()
        source = self._get_source()
        method = getattr(source, self.excel_method, None)
        if not self.excel_available or not method:
            raise UserError(_(
                'La exportación Excel no está disponible. Verifique que bi_financial_excel_reports esté instalado.'
            ))
        if self.excel_uses_report_type:
            source = source.with_context(report_type='excel', esi_html_preview=False)
            method = getattr(source, self.excel_method)
        result = method()

        # Los exportadores actuales crean un registro excel.report y abren un popup.
        # Desde la vista previa hacemos la descarga en un solo clic, sin perder la pantalla HTML.
        if (isinstance(result, dict) and result.get('type') == 'ir.actions.act_window'
                and result.get('res_model') == 'excel.report' and result.get('res_id')):
            return {
                'type': 'ir.actions.act_url',
                'url': (
                    '/web/content/?model=excel.report&id=%s&field=excel_file'
                    '&filename_field=file_name&download=true' % result['res_id']
                ),
                'target': 'self',
            }
        return result
