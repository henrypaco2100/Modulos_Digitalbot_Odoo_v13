# -*- coding: utf-8 -*-

from datetime import timedelta

import pytz

from odoo import api, fields, models
from odoo.osv.expression import AND


class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'

    @api.model
    def _sd_get_orders(self, date_start=False, date_stop=False,
                       config_ids=False, session_ids=False):
        """Return exactly the POS orders covered by Odoo 13 sale-details logic."""
        # ESI corrección: replicar el dominio nativo de Odoo 13 para que el detalle
        # por línea use exactamente los mismos pedidos que el total oficial.
        domain = [('state', 'in', ['paid', 'invoiced', 'done'])]

        if session_ids:
            domain = AND([domain, [('session_id', 'in', session_ids)]])
        else:
            if date_start:
                date_start = fields.Datetime.from_string(date_start)
            else:
                user_tz = pytz.timezone(
                    self.env.context.get('tz') or self.env.user.tz or 'UTC'
                )
                today = user_tz.localize(
                    fields.Datetime.from_string(fields.Date.context_today(self))
                )
                date_start = today.astimezone(pytz.timezone('UTC'))

            if date_stop:
                date_stop = fields.Datetime.from_string(date_stop)
                if date_stop < date_start:
                    date_stop = date_start + timedelta(days=1, seconds=-1)
            else:
                date_stop = date_start + timedelta(days=1, seconds=-1)

            domain = AND([
                domain,
                [
                    ('date_order', '>=', fields.Datetime.to_string(date_start)),
                    ('date_order', '<=', fields.Datetime.to_string(date_stop)),
                ],
            ])

            if config_ids:
                domain = AND([domain, [('config_id', 'in', config_ids)]])

        return self.env['pos.order'].search(domain, order='date_order, id')

    @api.model
    def _sd_build_detailed_lines(self, orders):
        """Build non-aggregated sales lines with order date and payment method."""
        user_currency = self.env.company.currency_id
        detailed_lines = []

        for order in orders:
            # ESI corrección: una venta puede tener pago dividido. No se duplica la
            # línea (eso alteraría cantidades/totales); se muestran todos los métodos.
            payment_method_names = []
            for payment in order.payment_ids.sorted(key=lambda p: p.id):
                method_name = payment.payment_method_id.name
                if method_name and method_name not in payment_method_names:
                    payment_method_names.append(method_name)
            payment_method = ' / '.join(payment_method_names)

            order_currency = order.pricelist_id.currency_id
            for line in order.lines.sorted(key=lambda l: l.id):
                price_unit = line.price_unit
                subtotal = line.price_subtotal_incl

                # ESI corrección: el total nativo de Odoo 13 se expresa en la moneda
                # de la compañía. Convertimos también cada línea cuando corresponde.
                if user_currency != order_currency:
                    conversion_date = order.date_order or fields.Date.today()
                    price_unit = order_currency._convert(
                        price_unit,
                        user_currency,
                        order.company_id,
                        conversion_date,
                    )
                    subtotal = order_currency._convert(
                        subtotal,
                        user_currency,
                        order.company_id,
                        conversion_date,
                    )

                detailed_lines.append({
                    'line_id': line.id,
                    'order_id': order.id,
                    'order_name': order.name,
                    'date': order.date_order,
                    'payment_method': payment_method,
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name,
                    'code': line.product_id.default_code,
                    'quantity': line.qty,
                    'price_unit': price_unit,
                    'discount': line.discount,
                    'subtotal': subtotal,
                    'uom': line.product_id.uom_id.name,
                })

        return detailed_lines

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False,
                         config_ids=False, session_ids=False):
        """Extend Odoo's native result with a real line-by-line dataset."""
        # ESI corrección: conservar la lógica oficial de Odoo para total, pagos,
        # impuestos y moneda; únicamente añadimos el detalle sin agrupar.
        result = super(ReportSaleDetails, self).get_sale_details(
            date_start=date_start,
            date_stop=date_stop,
            config_ids=config_ids,
            session_ids=session_ids,
        )
        orders = self._sd_get_orders(
            date_start=date_start,
            date_stop=date_stop,
            config_ids=config_ids,
            session_ids=session_ids,
        )
        detailed_lines = self._sd_build_detailed_lines(orders)
        detailed_total = self.env.company.currency_id.round(
            sum(line['subtotal'] for line in detailed_lines)
        )
        # ESI corrección: guardar también una diferencia de control para Excel.
        # El total oficial sigue siendo total_paid, calculado por la lógica nativa de Odoo.
        total_difference = self.env.company.currency_id.round(
            (result.get('total_paid') or 0.0) - detailed_total
        )
        result.update({
            'detailed_lines': detailed_lines,
            'detailed_total': detailed_total,
            'total_difference': total_difference,
        })
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Extend Odoo 13's report bridge so ``session_ids`` is respected by HTML,
        PDF and Excel, while keeping Odoo's native total/payment/tax logic.
        """
        data = dict(data or {})

        configs = self.env['pos.config'].browse(data.get('config_ids', []))
        sessions = self.env['pos.session'].browse(
            data.get('session_ids', [])
        ).exists()

        data['session_ids'] = sessions.ids
        data['session_names'] = sessions.mapped('name')

        # ESI corrección: exponer los POS efectivos también al Excel/resumen.
        effective_configs = sessions.mapped('config_id') if sessions else configs
        data['config_names'] = effective_configs.mapped('name')

        # ESI corrección: si se seleccionan sesiones, Odoo 13 ignora el rango de
        # fechas y toma la sesión completa. El encabezado debe mostrar ese rango real.
        if sessions:
            session_starts = [start for start in sessions.mapped('start_at') if start]
            session_stops = [
                stop or fields.Datetime.now() for stop in sessions.mapped('stop_at')
            ]
            if session_starts:
                data['date_start'] = min(session_starts)
            if session_stops:
                data['date_stop'] = max(session_stops)

        data.update(self.get_sale_details(
            data.get('date_start'),
            data.get('date_stop'),
            configs.ids,
            sessions.ids,
        ))
        return data
