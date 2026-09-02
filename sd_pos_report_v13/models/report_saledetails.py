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
    def _sd_line_uom_values(self, line):
        """Resolve sale UOM and base-equivalent quantity without hard dependency."""
        base_uom = line.product_id.uom_id
        sale_uom = base_uom

        # ESI corrección: pos_multi_uom guarda la UDM seleccionada en product_uom.
        # Se detecta dinámicamente para que este módulo siga funcionando también
        # cuando pos_multi_uom no está instalado.
        if 'product_uom' in line._fields and line.product_uom:
            sale_uom = line.product_uom

        base_qty = line.qty
        uom_to_base_factor = 1.0
        if (
            sale_uom
            and base_uom
            and sale_uom.category_id == base_uom.category_id
        ):
            base_qty = sale_uom._compute_quantity(
                line.qty,
                base_uom,
                round=False,
            )
            # ESI corrección: factor equivalente de UNA UDM vendida a la UDM base.
            # Se usa para ordenar, por ejemplo, CAJA (24) antes de Unidades (1).
            uom_to_base_factor = sale_uom._compute_quantity(
                1.0,
                base_uom,
                round=False,
            )

        return sale_uom, base_uom, base_qty, uom_to_base_factor

    @api.model
    def _sd_build_detailed_lines(self, orders):
        """Build non-aggregated sales lines with date, payment and real sale UOM."""
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

                sale_uom, base_uom, base_qty, uom_to_base_factor = self._sd_line_uom_values(line)

                detailed_lines.append({
                    'line_id': line.id,
                    'order_id': order.id,
                    'order_name': order.name,
                    'date': order.date_order,
                    'payment_method': payment_method,
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name,
                    'code': line.product_id.default_code,
                    # ESI corrección: en Detallado respetar lo que realmente vendió
                    # el cajero: 2 Cajas, 3 Paquetes, 1 Unidad, etc.
                    'quantity': line.qty,
                    'uom': sale_uom.name if sale_uom else '',
                    'uom_id': sale_uom.id if sale_uom else False,
                    # ESI corrección: equivalencia para el modo Totales. Ejemplo:
                    # 2 Cajas de 24 = 48 Unidades base.
                    'base_quantity': base_qty,
                    'base_uom': base_uom.name if base_uom else '',
                    'base_uom_id': base_uom.id if base_uom else False,
                    'uom_to_base_factor': uom_to_base_factor,
                    'price_unit': price_unit,
                    'discount': line.discount,
                    'subtotal': subtotal,
                })

        return detailed_lines

    @api.model
    def _sd_build_total_lines(self, detailed_lines):
        """Aggregate same product using its base UOM to avoid mixing Caja/Unidad."""
        # ESI corrección: no se puede sumar 2 Cajas + 3 Unidades como "5 Unidades".
        # Para Totales convertimos cada venta a la UDM base y recién después sumamos.
        # Así 2 Cajas de 24 + 3 Unidades = 51 Unidades.
        products = {}
        for line in detailed_lines:
            key = line['product_id']
            row = products.setdefault(key, {
                'product_id': line['product_id'],
                'product_name': line['product_name'],
                'code': line['code'],
                'quantity': 0.0,
                'price_total': 0.0,
                'uom': line['base_uom'],
                'uom_id': line['base_uom_id'],
            })
            row['quantity'] += line['base_quantity']
            row['price_total'] += line['subtotal']

        return sorted(products.values(), key=lambda row: (row['product_name'] or '').lower())

    @api.model
    def _sd_build_total_detailed_lines(self, detailed_lines):
        """Aggregate by product + sale UOM while preserving the sold unit."""
        # ESI corrección: nueva opción "Total - detallado".
        # No mezcla Cajas con Unidades y tampoco repite cada ticket.
        # Ejemplo:
        #   PACEÑA NORMAL | 2 | CAJA     | 215 | 430
        #   PACEÑA NORMAL | 3 | Unidades | 12  | 36
        grouped = {}
        for line in detailed_lines:
            key = (line['product_id'], line.get('uom_id') or 0)
            row = grouped.setdefault(key, {
                'product_id': line['product_id'],
                'product_name': line['product_name'],
                'code': line['code'],
                'quantity': 0.0,
                'uom': line.get('uom') or '',
                'uom_id': line.get('uom_id') or False,
                'uom_to_base_factor': line.get('uom_to_base_factor') or 1.0,
                'price_total': 0.0,
                '_weighted_price_unit': 0.0,
            })
            qty = line.get('quantity') or 0.0
            row['quantity'] += qty
            row['price_total'] += line.get('subtotal') or 0.0
            row['_weighted_price_unit'] += (line.get('price_unit') or 0.0) * qty

        rows = []
        for row in grouped.values():
            qty = row['quantity']
            # ESI corrección: si hubo distintas tarifas en la misma UDM, mostrar
            # un precio unitario promedio ponderado sin alterar el precio total real.
            row['price_unit'] = (
                row['_weighted_price_unit'] / qty if qty else 0.0
            )
            row.pop('_weighted_price_unit', None)
            rows.append(row)

        # Mismo producto junto; UDM grandes primero (Caja antes de Unidad).
        return sorted(
            rows,
            key=lambda row: (
                (row['product_name'] or '').lower(),
                -(row.get('uom_to_base_factor') or 1.0),
                (row.get('uom') or '').lower(),
            ),
        )

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False,
                         config_ids=False, session_ids=False):
        """Extend Odoo native result with detailed + product-total datasets."""
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
        total_lines = self._sd_build_total_lines(detailed_lines)
        total_detailed_lines = self._sd_build_total_detailed_lines(detailed_lines)
        currency = self.env.company.currency_id

        detailed_total = currency.round(sum(line['subtotal'] for line in detailed_lines))
        total_difference = currency.round(
            (result.get('total_paid') or 0.0) - detailed_total
        )
        result.update({
            'detailed_lines': detailed_lines,
            'total_lines': total_lines,
            'total_detailed_lines': total_detailed_lines,
            'detailed_total': detailed_total,
            'total_difference': total_difference,
        })
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        """Bridge session/type filters to HTML, PDF and Excel."""
        data = dict(data or {})

        configs = self.env['pos.config'].browse(data.get('config_ids', []))
        sessions = self.env['pos.session'].browse(data.get('session_ids', [])).exists()

        report_type = data.get('report_type') or 'totals'
        if report_type not in ('totals', 'total_detailed', 'detailed'):
            report_type = 'totals'
        data['report_type'] = report_type
        data['report_type_label'] = {
            'totals': 'Totales',
            'total_detailed': 'Total - detallado',
            'detailed': 'Detallado',
        }[report_type]

        data['session_ids'] = sessions.ids
        data['session_names'] = sessions.mapped('name')

        effective_configs = sessions.mapped('config_id') if sessions else configs
        data['config_names'] = effective_configs.mapped('name')

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
