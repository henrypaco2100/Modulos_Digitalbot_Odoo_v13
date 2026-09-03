# -*- coding: utf-8 -*-

from datetime import timedelta

import pytz

from odoo import api, fields, models
from odoo.tools.float_utils import float_round
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
    def _sd_get_decimal_precision(self, precision_name, default=2):
        """Return Odoo Technical > Decimal Accuracy precision safely."""
        # ESI corrección: Odoo 13 administra estas precisiones en el modelo
        # decimal.precision (Ajustes > Técnico > Estructura de la base de datos
        # > Precisión decimal). Si no existe el registro, usamos 2 decimales.
        try:
            digits = self.env['decimal.precision'].precision_get(precision_name)
        except Exception:
            digits = default
        return int(digits if digits is not False and digits is not None else default)

    @api.model
    def _sd_round_quantity(self, quantity, uom=False):
        """Round a quantity with the UDM precision and return a clean display."""
        # ESI corrección: no mostramos 6 decimales fijos ni ruido binario.
        # La cantidad se redondea y se presenta con la precisión técnica de Odoo
        # "Product Unit of Measure". Por defecto son 2 decimales.
        digits = self._sd_get_decimal_precision('Product Unit of Measure', 2)
        clean_qty = float_round(quantity or 0.0, precision_digits=digits)
        qty_display = ('%.*f' % (digits, clean_qty))
        if clean_qty == 0:
            qty_display = '%.*f' % (digits, 0.0)
        return clean_qty, qty_display

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
                clean_qty, quantity_display = self._sd_round_quantity(line.qty, sale_uom)
                clean_base_qty, base_quantity_display = self._sd_round_quantity(base_qty, base_uom)

                # ESI corrección: precio realmente cobrado por cada UDM vendida.
                # Se obtiene del subtotal real de Odoo, por lo que también distingue
                # cambios de precio hechos mediante descuento. Ej.: 12 Bs, 11 Bs,
                # Caja 260 Bs y Caja 270 Bs quedan como grupos independientes.
                effective_price_unit = (subtotal / line.qty) if line.qty else price_unit
                # ESI corrección: el precio unitario respeta la precisión técnica
                # "Product Price" de Odoo, no una cantidad arbitraria de decimales.
                price_digits = self._sd_get_decimal_precision('Product Price', 2)
                effective_price_unit = float_round(
                    effective_price_unit, precision_digits=price_digits
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
                    # ESI corrección: en Detallado respetar lo que realmente vendió
                    # el cajero: 2 Cajas, 3 Paquetes, 1 Unidad, etc.
                    'quantity': clean_qty,
                    'quantity_display': quantity_display,
                    'uom': sale_uom.name if sale_uom else '',
                    'uom_id': sale_uom.id if sale_uom else False,
                    # ESI corrección: equivalencia para el modo Totales. Ejemplo:
                    # 2 Cajas de 24 = 48 Unidades base.
                    'base_quantity': clean_base_qty,
                    'base_quantity_display': base_quantity_display,
                    'base_uom': base_uom.name if base_uom else '',
                    'base_uom_id': base_uom.id if base_uom else False,
                    'uom_to_base_factor': uom_to_base_factor,
                    'price_unit': price_unit,
                    'effective_price_unit': effective_price_unit,
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

        rows = []
        for row in products.values():
            uom = self.env['uom.uom'].browse(row['uom_id']) if row.get('uom_id') else False
            row['quantity'], row['quantity_display'] = self._sd_round_quantity(row['quantity'], uom)
            rows.append(row)

        return sorted(rows, key=lambda row: (row['product_name'] or '').lower())

    @api.model
    def _sd_build_total_detailed_lines(self, detailed_lines):
        """Aggregate by product + sale UOM + actual unit sale price."""
        # ESI corrección: "Total - precio unitario - UDM" separa también por el precio
        # real cobrado. No se promedian precios distintos. Ejemplo:
        #   PACEÑA | 4 | Unidades | 12.00 | 48.00
        #   PACEÑA | 1 | Unidades | 11.00 | 11.00
        #   PACEÑA | 2 | CAJA     | 260.00 | 520.00
        #   PACEÑA | 1 | CAJA     | 270.00 | 270.00
        grouped = {}
        currency = self.env.company.currency_id
        price_digits = self._sd_get_decimal_precision('Product Price', 2)

        for line in detailed_lines:
            effective_price = float_round(
                line.get('effective_price_unit') or 0.0,
                precision_digits=price_digits,
            )
            # El precio redondeado de moneda forma parte de la clave para evitar
            # grupos falsamente distintos por ruido decimal de Python.
            key = (
                line['product_id'],
                line.get('uom_id') or 0,
                effective_price,
            )
            row = grouped.setdefault(key, {
                'product_id': line['product_id'],
                'product_name': line['product_name'],
                'code': line['code'],
                'quantity': 0.0,
                'uom': line.get('uom') or '',
                'uom_id': line.get('uom_id') or False,
                'uom_to_base_factor': line.get('uom_to_base_factor') or 1.0,
                'price_unit': effective_price,
                'price_total': 0.0,
            })
            row['quantity'] += line.get('quantity') or 0.0
            row['price_total'] += line.get('subtotal') or 0.0

        rows = []
        for row in grouped.values():
            uom = self.env['uom.uom'].browse(row['uom_id']) if row.get('uom_id') else False
            row['quantity'], row['quantity_display'] = self._sd_round_quantity(
                row['quantity'], uom
            )
            row['price_unit'] = float_round(row['price_unit'], precision_digits=price_digits)
            row['price_total'] = currency.round(row['price_total'])
            rows.append(row)

        # Producto junto; UDM grandes primero (Caja antes de Unidad), y dentro
        # de la misma UDM cada precio de venta queda en una línea independiente.
        return sorted(
            rows,
            key=lambda row: (
                (row['product_name'] or '').lower(),
                -(row.get('uom_to_base_factor') or 1.0),
                row.get('price_unit') or 0.0,
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
            'totals': 'Total',
            'total_detailed': 'Total - precio unitario - UDM',
            'detailed': 'Total detallado',
        }[report_type]

        # ESI corrección: exponer precisiones técnicas para HTML/PDF/Excel.
        data['uom_precision'] = self._sd_get_decimal_precision(
            'Product Unit of Measure', 2
        )
        data['price_precision'] = self._sd_get_decimal_precision('Product Price', 2)
        currency = self.env.company.currency_id
        data['currency_precision'] = int(currency.decimal_places or 2)

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
