# -*- coding: utf-8 -*-

import io
from collections import defaultdict
from datetime import datetime, time

import pytz
import xlsxwriter

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class KardexReport(models.TransientModel):
    _name = 'kardex.report'
    _description = 'Reporte Kardex Físico Valorado'

    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True, default=lambda self: self.env.user.company_id
    )
    date_start = fields.Date(string='Fecha inicio')
    date_end = fields.Date(string='Fecha Final')
    categ_id = fields.Many2many('product.category', string='Categoria de Producto')

    sinvariantes = fields.Boolean(string='Separar variantes de productos')
    filtraralmacenes = fields.Boolean(string='Agrupar almacenes', default=False)
    filtrarcategorias = fields.Boolean(string='Agrupar categorias')
    filtrartipomov = fields.Boolean(string='tipo/concepto', default=False, readonly=True)
    filtrarproductos = fields.Boolean(string='Filtrar productos')
    mostrar_ubicaciones = fields.Boolean(
        string='Mostrar ubicaciones origen/destino', default=False, readonly=True
    )
    sd_notdetails = fields.Boolean(string='Detalles de movimientos', default=False)
    sd_notdocuments = fields.Boolean(string='Documento Origen', default=False, readonly=True)

    seleccionalmacenes = fields.Many2many('stock.warehouse', string='Seleccion de almacenes')
    seleccionproductos = fields.Many2many('product.product', string='Seleccion de productos')

    # ESI corrección: selección múltiple de unidades de medida. Cada unidad seleccionada
    # se convierte en una columna dinámica inmediatamente después de PRODUCTO.
    uom_ids = fields.Many2many(
        'uom.uom',
        'kardex_report_uom_rel',
        'report_id',
        'uom_id',
        string='Unidad de medida',
        help=(
            'Las columnas seleccionadas muestran el saldo acumulado convertido a cada '
            'unidad de medida compatible con el producto.'
        ),
    )

    # Se mantienen por compatibilidad con instalaciones anteriores del módulo.
    excel_file = fields.Binary('Reporte Excel', readonly=True)
    file_name = fields.Char('Archivo Excel', size=128, readonly=True)

    @api.onchange('sd_notdetails')
    def change_details(self):
        for wizard in self:
            if wizard.sd_notdetails:
                wizard.sd_notdocuments = True
                wizard.mostrar_ubicaciones = True
                wizard.filtrartipomov = True
            else:
                wizard.sd_notdocuments = False
                wizard.mostrar_ubicaciones = False
                wizard.filtrartipomov = False

    # -------------------------------------------------------------------------
    # Acciones del wizard: VER / PDF / EXCEL
    # -------------------------------------------------------------------------
    def _validate_report(self):
        self.ensure_one()
        if (
            self.date_start
            and self.date_end
            and self._date_value(self.date_start) > self._date_value(self.date_end)
        ):
            raise UserError(_('La Fecha inicio no puede ser mayor que la Fecha Final.'))

    def action_view_kardex(self):
        """ESI corrección: vista previa HTML antes de descargar."""
        self._validate_report()
        return self.env.ref('st_kardex.kardex_product_report_html').report_action(self)

    def action_report_pdf(self):
        """Descarga directa del PDF generado con exactamente la misma lógica del HTML."""
        self._validate_report()
        return {
            'type': 'ir.actions.act_url',
            'url': '/st_kardex/pdf/%s' % self.id,
            'target': 'self',
        }

    def action_report_kardex(self):
        """Descarga directa del XLSX generado con exactamente la misma lógica del HTML."""
        self._validate_report()
        return {
            'type': 'ir.actions.act_url',
            'url': '/st_kardex/excel/%s' % self.id,
            'target': 'self',
        }

    # -------------------------------------------------------------------------
    # Filtros y utilidades
    # -------------------------------------------------------------------------
    def _date_value(self, value):
        if not value:
            return False
        if isinstance(value, str):
            return fields.Date.from_string(value)
        return value

    def _get_utc_bounds(self):
        """
        ESI corrección: reemplaza el +4 horas fijo por la zona horaria real del usuario.
        Odoo guarda datetimes en UTC sin tzinfo.
        """
        self.ensure_one()
        tz_name = self.env.user.tz or self.env.user.company_id.partner_id.tz or 'UTC'
        try:
            timezone = pytz.timezone(tz_name)
        except Exception:
            timezone = pytz.UTC

        start_utc = False
        end_utc = False
        start_date = self._date_value(self.date_start)
        end_date = self._date_value(self.date_end)

        if start_date:
            start_local = timezone.localize(datetime.combine(start_date, time.min))
            start_utc = start_local.astimezone(pytz.UTC).replace(tzinfo=None)
        if end_date:
            end_local = timezone.localize(datetime.combine(end_date, time.max))
            end_utc = end_local.astimezone(pytz.UTC).replace(tzinfo=None)
        return start_utc, end_utc

    def _local_datetime_string(self, value):
        if not value:
            return ''
        if isinstance(value, str):
            value = fields.Datetime.from_string(value)
        local_dt = fields.Datetime.context_timestamp(self, value)
        return local_dt.strftime('%d/%m/%Y %H:%M')

    def _selected_uoms(self):
        return self.uom_ids.sorted(key=lambda u: (u.category_id.name or '', u.name or '', u.id))

    def _selected_warehouses(self):
        warehouses = self.seleccionalmacenes
        if not warehouses:
            warehouses = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)])
        return warehouses

    def _product_filter_domain(self, field_name='product_id'):
        domain = []
        if self.seleccionproductos:
            domain.append((field_name, 'in', self.seleccionproductos.ids))
        elif self.categ_id:
            categories = self.env['product.category'].search([('id', 'child_of', self.categ_id.ids)])
            domain.append(('%s.categ_id' % field_name, 'in', categories.ids))
        return domain

    def _product_group_key(self, product):
        if self.sinvariantes:
            return 'product_%s' % product.id
        return 'template_%s' % product.product_tmpl_id.id

    def _product_report_name(self, product):
        if self.sinvariantes:
            return product.display_name
        return product.product_tmpl_id.display_name

    def _product_category(self, product):
        return product.product_tmpl_id.categ_id

    def _warehouse_from_move(self, move, origin=True):
        field_name = 'sd_almacen_origen' if origin else 'sd_almacen_destino'
        warehouse = getattr(move, field_name, False)
        if warehouse:
            return warehouse[:1]

        # Respaldo para movimientos antiguos que todavía no tienen los campos ESI llenados.
        location = move.location_id if origin else move.location_dest_id
        get_warehouse = getattr(move, 'get_warehouse_id', False)
        if get_warehouse and location:
            try:
                warehouse = get_warehouse(location)
                return warehouse[:1]
            except Exception:
                return self.env['stock.warehouse']
        return self.env['stock.warehouse']

    def _movement_type(self, move):
        origin = move.location_id.usage or ''
        dest = move.location_dest_id.usage or ''
        switcher = {
            'supplier_internal': 'Compra',
            'transit_internal': 'Entrada desde tránsito',
            'customer_internal': 'Devolución de cliente',
            'internal_customer': 'Venta',
            'internal_supplier': 'Devolución a proveedor',
            'internal_transit': 'Salida a tránsito',
            'internal_inventory': 'Ajuste de inventario de salida',
            'inventory_internal': 'Ajuste de inventario de entrada',
            'internal_internal': 'Transferencia interna',
            'production_internal': 'Producción para almacén',
            'internal_production': 'Materia prima para producción',
        }
        concept = switcher.get('%s_%s' % (origin, dest), 'Movimiento de inventario')

        # Si es un desecho, se identifica expresamente para que el concepto sea claro.
        if origin == 'internal' and dest == 'inventory' and 'scrap_ids' in move._fields:
            if move.scrap_ids:
                concept = 'Desecho'
        return concept

    def _movement_document(self, move):
        parts = []

        def append(value):
            if value and value not in parts:
                parts.append(value)

        append(move.picking_id.name if move.picking_id else False)
        if 'purchase_line_id' in move._fields and move.purchase_line_id:
            append(move.purchase_line_id.order_id.name)
        if 'sale_line_id' in move._fields and move.sale_line_id:
            append(move.sale_line_id.order_id.name)
        if 'inventory_id' in move._fields and move.inventory_id:
            append(move.inventory_id.name)
        if 'production_id' in move._fields and move.production_id:
            append(move.production_id.name)
        append(move.origin)
        append(move.reference)
        return ' - '.join(parts)

    def _move_quantity_base_uom(self, move):
        """Cantidad del movimiento expresada en la U.M. base del producto."""
        primary_layers = move.stock_valuation_layer_ids.filtered(lambda layer: layer.quantity)
        qty = abs(sum(primary_layers.mapped('quantity'))) if primary_layers else 0.0
        if qty:
            return qty

        qty_done = abs(move.quantity_done or move.product_uom_qty or 0.0)
        product_uom = move.product_id.uom_id
        move_uom = move.product_uom
        if move_uom and product_uom and move_uom.category_id == product_uom.category_id:
            try:
                return abs(move_uom._compute_quantity(qty_done, product_uom, round=False))
            except TypeError:
                return abs(move_uom._compute_quantity(qty_done, product_uom))
        return qty_done

    def _historical_transfer_unit_cost(self, product, date):
        """Costo promedio histórico como respaldo para transferencias internas sin SVL de valor."""
        if not product or not date:
            return 0.0
        query = """
            WITH avg_value AS (
                SELECT CASE
                    WHEN COALESCE(SUM(quantity), 0) = 0 THEN 0
                    ELSE SUM(value) / SUM(quantity)
                END AS average_value
                FROM stock_valuation_layer
                WHERE product_id = %s AND company_id = %s AND create_date <= %s
            ),
            last_positive_value AS (
                SELECT CASE WHEN quantity = 0 THEN 0 ELSE value / quantity END AS last_avg_value
                FROM stock_valuation_layer
                WHERE product_id = %s AND company_id = %s AND quantity > 0 AND create_date <= %s
                ORDER BY create_date DESC
                LIMIT 1
            )
            SELECT CASE
                WHEN avg_value.average_value = 0 THEN COALESCE(last_positive_value.last_avg_value, 0)
                ELSE avg_value.average_value
            END AS final_value
            FROM avg_value
            LEFT JOIN last_positive_value ON TRUE
        """
        self.env.cr.execute(
            query,
            (product.id, self.company_id.id, date, product.id, self.company_id.id, date),
        )
        result = self.env.cr.fetchone()
        return abs(result[0] or 0.0) if result else 0.0

    def _move_value_amount(self, move, qty):
        """
        Valor principal del movimiento. Los SVL con cantidad cero se procesan como ajustes
        independientes en su fecha de creación para no distorsionar históricos.
        """
        primary_layers = move.stock_valuation_layer_ids.filtered(lambda layer: layer.quantity)
        value = abs(sum(primary_layers.mapped('value'))) if primary_layers else 0.0
        if value:
            return value

        if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'internal':
            return self._historical_transfer_unit_cost(move.product_id, move.date) * qty
        return 0.0

    def _bucket_deltas_for_move(self, move, qty, warehouses):
        """
        Retorna [(bucket_id, warehouse_record|False, qty_delta)].

        ESI corrección lógica:
        - Global: una transferencia entre almacenes seleccionados no cambia el inventario total.
        - Agrupado: sale del almacén origen y entra al almacén destino.
        - Un traslado entre ubicaciones del mismo almacén no duplica cantidades.
        """
        selected_ids = set(warehouses.ids)
        origin_wh = self._warehouse_from_move(move, origin=True)
        dest_wh = self._warehouse_from_move(move, origin=False)
        origin_id = origin_wh.id if origin_wh else False
        dest_id = dest_wh.id if dest_wh else False

        if self.filtraralmacenes:
            deltas = []
            if origin_id in selected_ids and origin_id != dest_id:
                deltas.append((origin_id, origin_wh, -qty))
            if dest_id in selected_ids and dest_id != origin_id:
                deltas.append((dest_id, dest_wh, qty))
            return deltas

        # En modo global, si no se eligieron almacenes se consideran también ubicaciones
        # internas que por alguna configuración antigua no estén ligadas a stock.warehouse.
        include_unmapped_internal = not bool(self.seleccionalmacenes)
        origin_inside = (
            move.location_id.usage == 'internal'
            and (origin_id in selected_ids or (include_unmapped_internal and not origin_id))
        )
        dest_inside = (
            move.location_dest_id.usage == 'internal'
            and (dest_id in selected_ids or (include_unmapped_internal and not dest_id))
        )

        if origin_inside and not dest_inside:
            return [('global', False, -qty)]
        if dest_inside and not origin_inside:
            return [('global', False, qty)]
        return []

    def _convert_qty(self, product, qty, target_uom):
        source_uom = product.uom_id
        if not source_uom or not target_uom or source_uom.category_id != target_uom.category_id:
            return None
        try:
            return source_uom._compute_quantity(qty, target_uom, round=False)
        except TypeError:
            return source_uom._compute_quantity(qty, target_uom)

    def _uom_values(self, product, qty, selected_uoms):
        return [self._convert_qty(product, qty, uom) for uom in selected_uoms]

    # -------------------------------------------------------------------------
    # Motor único de cálculo para HTML / PDF / Excel
    # -------------------------------------------------------------------------
    def _empty_state(self, bucket_id, warehouse, product):
        category = self._product_category(product)
        return {
            'bucket_id': bucket_id,
            'warehouse_id': warehouse.id if warehouse else False,
            'warehouse_name': warehouse.display_name if warehouse else _('Kardex global'),
            'product_key': self._product_group_key(product),
            'product': product,
            'product_name': self._product_report_name(product),
            'category_id': category.id,
            'category_name': category.display_name,
            'qty': 0.0,
            'value': 0.0,
            'last_datetime': False,
        }

    def _state_key(self, bucket_id, product):
        return (bucket_id, self._product_group_key(product))

    def _get_state(self, states, bucket_id, warehouse, product):
        key = self._state_key(bucket_id, product)
        if key not in states:
            states[key] = self._empty_state(bucket_id, warehouse, product)
        return key, states[key]

    def _line_from_state(
        self,
        state,
        selected_uoms,
        event_dt,
        concept,
        qty_delta=0.0,
        value_delta=0.0,
        origin='',
        dest='',
        document='',
        event_order=10,
    ):
        entry_qty = qty_delta if qty_delta > 0 else 0.0
        output_qty = abs(qty_delta) if qty_delta < 0 else 0.0
        entry_value = value_delta if value_delta > 0 else 0.0
        output_value = abs(value_delta) if value_delta < 0 else 0.0
        balance_qty = state['qty']
        balance_value = state['value']

        return {
            'warehouse_id': state['warehouse_id'],
            'warehouse_name': state['warehouse_name'],
            'category_id': state['category_id'],
            'category_name': state['category_name'],
            'product_key': state['product_key'],
            'product_name': state['product_name'],
            'event_dt': event_dt,
            'event_order': event_order,
            'date': self._local_datetime_string(event_dt) if event_dt else '',
            'concept': concept,
            'origin': origin,
            'dest': dest,
            'document': document,
            'uom_values': self._uom_values(state['product'], balance_qty, selected_uoms),
            'entry_qty': entry_qty,
            'entry_unit': (entry_value / entry_qty) if entry_qty else 0.0,
            'entry_total': entry_value,
            'output_qty': output_qty,
            'output_unit': (output_value / output_qty) if output_qty else 0.0,
            'output_total': output_value,
            'balance_qty': balance_qty,
            'balance_unit': (balance_value / balance_qty) if balance_qty else 0.0,
            'balance_total': balance_value,
            'is_last': False,
            'nro': 0,
        }

    def _apply_move_event(self, states, move, warehouses, selected_uoms, create_line=False):
        product = move.product_id
        qty = self._move_quantity_base_uom(move)
        if not product or not qty:
            return [], set()

        value_amount = self._move_value_amount(move, qty)
        concept = self._movement_type(move)
        origin = move.location_id.complete_name or move.location_id.display_name
        dest = move.location_dest_id.complete_name or move.location_dest_id.display_name
        document = self._movement_document(move)
        lines = []
        touched = set()

        for bucket_id, warehouse, qty_delta in self._bucket_deltas_for_move(move, qty, warehouses):
            key, state = self._get_state(states, bucket_id, warehouse, product)
            value_delta = value_amount if qty_delta > 0 else -value_amount
            state['qty'] += qty_delta
            state['value'] += value_delta
            state['last_datetime'] = move.date
            touched.add(key)
            if create_line:
                lines.append(
                    self._line_from_state(
                        state,
                        selected_uoms,
                        move.date,
                        concept,
                        qty_delta=qty_delta,
                        value_delta=value_delta,
                        origin=origin,
                        dest=dest,
                        document=document,
                        event_order=20,
                    )
                )
        return lines, touched

    def _adjustment_target_warehouse(self, layer, warehouses):
        if not self.filtraralmacenes or not layer.stock_move_id:
            return self.env['stock.warehouse']
        move = layer.stock_move_id
        target = self.env['stock.warehouse']
        if move.location_dest_id.usage == 'internal':
            target = self._warehouse_from_move(move, origin=False)
        elif move.location_id.usage == 'internal':
            target = self._warehouse_from_move(move, origin=True)
        if target and target.id in warehouses.ids:
            return target
        return self.env['stock.warehouse']

    def _apply_adjustment_event(self, states, layer, warehouses, selected_uoms, create_line=False):
        product = layer.product_id
        adjustment_value = layer.value or 0.0
        if not product or not adjustment_value:
            return [], set(), False

        lines = []
        touched = set()
        warning = False

        if not self.filtraralmacenes:
            key, state = self._get_state(states, 'global', False, product)
            state['value'] += adjustment_value
            state['last_datetime'] = layer.create_date
            touched.add(key)
            if create_line:
                lines.append(
                    self._line_from_state(
                        state,
                        selected_uoms,
                        layer.create_date,
                        layer.description or _('Actualización de valoración'),
                        value_delta=adjustment_value,
                        document=layer.description or '',
                        event_order=30,
                    )
                )
            return lines, touched, warning

        target_wh = self._adjustment_target_warehouse(layer, warehouses)
        allocations = []
        if target_wh:
            key, state = self._get_state(states, target_wh.id, target_wh, product)
            allocations = [(key, state, adjustment_value)]
        else:
            # Si el ajuste no identifica almacén, se distribuye proporcionalmente al saldo
            # físico existente de ese producto en los almacenes seleccionados.
            candidates = []
            for key, state in states.items():
                if state['product_key'] == self._product_group_key(product) and state['warehouse_id'] in warehouses.ids:
                    weight = max(state['qty'], 0.0)
                    if weight:
                        candidates.append((key, state, weight))
            total_weight = sum(item[2] for item in candidates)
            if total_weight:
                allocations = [
                    (key, state, adjustment_value * weight / total_weight)
                    for key, state, weight in candidates
                ]
            else:
                warning = True

        for key, state, portion in allocations:
            state['value'] += portion
            state['last_datetime'] = layer.create_date
            touched.add(key)
            if create_line:
                lines.append(
                    self._line_from_state(
                        state,
                        selected_uoms,
                        layer.create_date,
                        layer.description or _('Actualización de valoración'),
                        value_delta=portion,
                        document=layer.description or '',
                        event_order=30,
                    )
                )
        return lines, touched, warning

    def _get_report_events(self, end_utc):
        move_domain = [('state', '=', 'done'), ('company_id', '=', self.company_id.id)]
        if end_utc:
            move_domain.append(('date', '<=', fields.Datetime.to_string(end_utc)))
        move_domain += self._product_filter_domain('product_id')
        moves = self.env['stock.move'].sudo().search(move_domain, order='date,id')

        adjustment_domain = [
            ('quantity', '=', 0),
            ('value', '!=', 0),
            ('company_id', '=', self.company_id.id),
        ]
        if end_utc:
            adjustment_domain.append(('create_date', '<=', fields.Datetime.to_string(end_utc)))
        adjustment_domain += self._product_filter_domain('product_id')
        adjustments = self.env['stock.valuation.layer'].sudo().search(
            adjustment_domain, order='create_date,id'
        )

        events = []
        for move in moves:
            events.append((move.date, 10, move.id, 'move', move))
        for layer in adjustments:
            events.append((layer.create_date, 20, layer.id, 'adjustment', layer))
        events.sort(key=lambda item: (item[0] or datetime.min, item[1], item[2]))
        return events

    def _snapshot_opening_lines(self, states, selected_uoms, start_utc):
        lines = []
        if not self.sd_notdetails or not start_utc:
            return lines
        for state in states.values():
            if abs(state['qty']) < 1e-9 and abs(state['value']) < 1e-9:
                continue
            lines.append(
                self._line_from_state(
                    state,
                    selected_uoms,
                    start_utc,
                    _('Saldo inicial'),
                    event_order=0,
                )
            )
        return lines

    def _final_lines(self, states, selected_uoms, visible_keys, end_utc):
        lines = []
        for key, state in states.items():
            if key not in visible_keys and abs(state['qty']) < 1e-9 and abs(state['value']) < 1e-9:
                continue
            event_dt = state['last_datetime'] or end_utc or datetime.now()
            lines.append(
                self._line_from_state(
                    state,
                    selected_uoms,
                    event_dt,
                    _('Saldo final'),
                    event_order=99,
                )
            )
        return lines

    def _build_sections(self, lines, states, selected_uoms):
        by_warehouse = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for line in lines:
            wh_key = line['warehouse_id'] or 'global'
            cat_key = (line['category_id'], line['category_name'])
            by_warehouse[wh_key][cat_key][line['product_key']].append(line)

        # Estado final por grupo para totalizar valores sin sumar cantidades incompatibles.
        state_lookup = {
            (state['warehouse_id'] or 'global', state['category_id'], state['product_key']): state
            for state in states.values()
        }

        sections = []
        warehouse_keys = sorted(
            by_warehouse.keys(),
            key=lambda key: (
                '' if key == 'global' else next(
                    (
                        state['warehouse_name']
                        for state in states.values()
                        if (state['warehouse_id'] or 'global') == key
                    ),
                    '',
                )
            ),
        )
        for wh_key in warehouse_keys:
            warehouse_name = _('Kardex global')
            for state in states.values():
                if (state['warehouse_id'] or 'global') == wh_key:
                    warehouse_name = state['warehouse_name']
                    break

            wh_section = {'name': warehouse_name, 'categories': [], 'total_value': 0.0}
            categories = by_warehouse[wh_key]
            for cat_key in sorted(categories.keys(), key=lambda item: item[1] or ''):
                cat_id, cat_name = cat_key
                cat_section = {'name': cat_name, 'products': [], 'total_value': 0.0}
                products = categories[cat_key]
                product_keys = sorted(
                    products.keys(),
                    key=lambda pkey: products[pkey][0]['product_name'] if products[pkey] else '',
                )
                for pkey in product_keys:
                    product_lines = sorted(
                        products[pkey],
                        key=lambda line: (
                            line['event_dt'] or datetime.min,
                            line['event_order'],
                        ),
                    )
                    for line in product_lines:
                        line['is_last'] = False
                    if product_lines:
                        product_lines[-1]['is_last'] = True
                    final_state = state_lookup.get((wh_key, cat_id, pkey))
                    final_value = final_state['value'] if final_state else product_lines[-1]['balance_total']
                    cat_section['products'].append(
                        {
                            'name': product_lines[0]['product_name'] if product_lines else '',
                            'lines': product_lines,
                            'final_value': final_value,
                        }
                    )
                    cat_section['total_value'] += final_value
                wh_section['categories'].append(cat_section)
                wh_section['total_value'] += cat_section['total_value']
            sections.append(wh_section)

        nro = 1
        for section in sections:
            if self.filtraralmacenes:
                nro = 1
            for category in section['categories']:
                for product in category['products']:
                    for line in product['lines']:
                        line['nro'] = nro
                        nro += 1
        return sections

    def get_kardex_render_data(self):
        """Única fuente de datos para VER, PDF y EXCEL."""
        self.ensure_one()
        self._validate_report()
        start_utc, end_utc = self._get_utc_bounds()
        selected_uoms = self._selected_uoms()
        warehouses = self._selected_warehouses()
        events = self._get_report_events(end_utc)

        states = {}
        visible_keys = set()
        warning_adjustment = False

        # 1) Construir saldo previo real, incluso si el producto no tiene movimientos en el rango.
        # Si no existe Fecha inicio NO se hace esta fase, porque todos los eventos pertenecen
        # al rango y se procesarán una sola vez en la fase 2.
        if start_utc:
            for event_dt, _priority, _event_id, event_type, record in events:
                if event_dt >= start_utc:
                    break
                if event_type == 'move':
                    self._apply_move_event(
                        states, record, warehouses, selected_uoms, create_line=False
                    )
                else:
                    _lines, _touched, warning = self._apply_adjustment_event(
                        states, record, warehouses, selected_uoms, create_line=False
                    )
                    warning_adjustment = warning_adjustment or warning

            # Solo los saldos previos realmente existentes deben aparecer si no hubo movimientos
            # en el rango; así se evitan productos históricos que terminaron en cero.
            for key, state in states.items():
                if abs(state['qty']) >= 1e-9 or abs(state['value']) >= 1e-9:
                    visible_keys.add(key)

        lines = self._snapshot_opening_lines(states, selected_uoms, start_utc)

        # 2) Movimientos del rango.
        in_range_keys = set()
        for event_dt, _priority, _event_id, event_type, record in events:
            if start_utc and event_dt < start_utc:
                continue
            if end_utc and event_dt > end_utc:
                continue
            if event_type == 'move':
                event_lines, touched = self._apply_move_event(
                    states, record, warehouses, selected_uoms, create_line=self.sd_notdetails
                )
            else:
                event_lines, touched, warning = self._apply_adjustment_event(
                    states, record, warehouses, selected_uoms, create_line=self.sd_notdetails
                )
                warning_adjustment = warning_adjustment or warning
            in_range_keys.update(touched)
            lines.extend(event_lines)

        visible_keys.update(in_range_keys)

        # 3) Sin detalle: una línea final por producto, incluyendo productos sin movimientos en rango.
        if not self.sd_notdetails:
            lines = self._final_lines(states, selected_uoms, visible_keys, end_utc)

        sections = self._build_sections(lines, states, selected_uoms)
        total_value = sum(section['total_value'] for section in sections)

        categories_label = ', '.join(self.categ_id.mapped('display_name')) or _('Todas')
        warehouse_label = ', '.join(warehouses.mapped('display_name')) or _('Todos')
        products_label = ', '.join(self.seleccionproductos.mapped('display_name')) or _('Todos')

        prefix_col_count = 4  # Nro, Fecha, Categoría, Producto
        if self.filtrartipomov:
            prefix_col_count += 1
        if self.mostrar_ubicaciones:
            prefix_col_count += 2
        if self.sd_notdocuments:
            prefix_col_count += 1
        prefix_col_count += len(selected_uoms)

        warnings = []
        if warning_adjustment and self.filtraralmacenes:
            warnings.append(
                _(
                    'Existen ajustes de valoración sin un almacén identificable y sin saldo físico '
                    'disponible para distribuirlos; dichos ajustes no se asignaron por almacén.'
                )
            )

        return {
            'title': _('REPORTE KARDEX FÍSICO VALORADO'),
            'company': self.company_id.name,
            'date_start': self._date_value(self.date_start).strftime('%d/%m/%Y') if self.date_start else _('Primer registro'),
            'date_end': self._date_value(self.date_end).strftime('%d/%m/%Y') if self.date_end else _('Fecha actual'),
            'warehouses_label': warehouse_label,
            'categories_label': categories_label,
            'products_label': products_label,
            'uoms': [{'id': uom.id, 'name': uom.name} for uom in selected_uoms],
            'sections': sections,
            'details': self.sd_notdetails,
            'show_concept': self.filtrartipomov,
            'show_locations': self.mostrar_ubicaciones,
            'show_document': self.sd_notdocuments,
            'group_warehouses': self.filtraralmacenes,
            'group_categories': self.filtrarcategorias,
            'prefix_col_count': prefix_col_count,
            'total_value': total_value,
            'warnings': warnings,
        }

    # -------------------------------------------------------------------------
    # Excel XLSX
    # -------------------------------------------------------------------------
    def _excel_filename(self):
        today = self._date_value(fields.Date.today())
        suffix = self._date_value(self.date_end).strftime('%Y-%m-%d') if self.date_end else today.strftime('%Y-%m-%d')
        return 'Reporte_Kardex_%s.xlsx' % suffix

    def _build_excel_content(self):
        self.ensure_one()
        data = self.get_kardex_render_data()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Kardex')

        fmt_title = workbook.add_format(
            {'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'border': 1}
        )
        fmt_meta_label = workbook.add_format({'bold': True, 'border': 1, 'valign': 'top'})
        fmt_meta = workbook.add_format({'border': 1, 'valign': 'top', 'text_wrap': True})
        fmt_header = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True}
        )
        fmt_group = workbook.add_format({'bold': True, 'border': 1})
        fmt_text = workbook.add_format({'border': 1, 'valign': 'top'})
        fmt_text_bold = workbook.add_format({'bold': True, 'border': 1, 'valign': 'top'})
        fmt_qty = workbook.add_format({'border': 1, 'num_format': '#,##0.0000'})
        fmt_qty_bold = workbook.add_format({'bold': True, 'border': 1, 'num_format': '#,##0.0000'})
        fmt_money = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        fmt_money_bold = workbook.add_format({'bold': True, 'border': 1, 'num_format': '#,##0.00'})
        fmt_total_label = workbook.add_format({'bold': True, 'align': 'right', 'border': 1})
        fmt_note = workbook.add_format({'italic': True, 'text_wrap': True})

        # Columnas base + columnas dinámicas de U.M. + valores.
        base_columns = [
            ('nro', 'Nro', 6),
            ('date', 'FECHA', 18),
            ('category', 'CATEGORIA', 24),
        ]
        if data['show_concept']:
            base_columns.append(('concept', 'CONCEPTO', 28))
        if data['show_locations']:
            base_columns.extend([('origin', 'ORIGEN', 28), ('dest', 'DESTINO', 28)])
        if data['show_document']:
            base_columns.append(('document', 'DOCUMENTO', 26))
        base_columns.append(('product', 'PRODUCTO', 34))
        for uom in data['uoms']:
            base_columns.append(('uom_%s' % uom['id'], uom['name'].upper(), 14))

        financial_columns = 9 if data['details'] else 3
        total_columns = len(base_columns) + financial_columns
        last_col = total_columns - 1

        worksheet.merge_range(0, 0, 1, last_col, data['title'], fmt_title)
        worksheet.write(2, 0, 'Rango de fechas:', fmt_meta_label)
        worksheet.merge_range(2, 1, 2, max(1, last_col // 3), '%s - %s' % (data['date_start'], data['date_end']), fmt_meta)
        company_start = max(2, last_col // 3 + 1)
        worksheet.write(2, company_start, 'Compañía:', fmt_meta_label)
        worksheet.merge_range(2, company_start + 1, 2, last_col, data['company'], fmt_meta)

        worksheet.write(3, 0, 'Almacenes:', fmt_meta_label)
        worksheet.merge_range(3, 1, 3, max(1, last_col // 2), data['warehouses_label'], fmt_meta)
        cat_start = max(2, last_col // 2 + 1)
        worksheet.write(3, cat_start, 'Categorías:', fmt_meta_label)
        worksheet.merge_range(3, cat_start + 1, 3, last_col, data['categories_label'], fmt_meta)

        header_row = 5
        for col, (_key, title, width) in enumerate(base_columns):
            worksheet.merge_range(header_row, col, header_row + 1, col, title, fmt_header)
            worksheet.set_column(col, col, width)

        finance_start = len(base_columns)
        if data['details']:
            worksheet.merge_range(header_row, finance_start, header_row, finance_start + 2, 'ENTRADAS', fmt_header)
            worksheet.merge_range(header_row, finance_start + 3, header_row, finance_start + 5, 'SALIDAS', fmt_header)
            worksheet.merge_range(header_row, finance_start + 6, header_row, finance_start + 8, 'SALDOS', fmt_header)
            subtitles = ['CANTIDAD', 'VR UNITARIO', 'VR TOTAL'] * 3
        else:
            worksheet.merge_range(header_row, finance_start, header_row, finance_start + 2, 'SALDOS', fmt_header)
            subtitles = ['CANTIDAD', 'VR UNITARIO', 'VR TOTAL']
        for offset, subtitle in enumerate(subtitles):
            worksheet.write(header_row + 1, finance_start + offset, subtitle, fmt_header)
            worksheet.set_column(finance_start + offset, finance_start + offset, 14)

        row = header_row + 2
        if data['uoms']:
            worksheet.merge_range(
                row,
                0,
                row,
                last_col,
                'U.M.: las columnas ubicadas después de PRODUCTO muestran el saldo acumulado convertido a cada unidad seleccionada.',
                fmt_note,
            )
            row += 1

        for warning in data['warnings']:
            worksheet.merge_range(row, 0, row, last_col, warning, fmt_note)
            row += 1

        for section in data['sections']:
            if data['group_warehouses']:
                worksheet.merge_range(row, 0, row, last_col, section['name'].upper(), fmt_group)
                row += 1
            for category in section['categories']:
                if data['group_categories']:
                    worksheet.merge_range(row, 0, row, last_col, category['name'].upper(), fmt_group)
                    row += 1
                for product in category['products']:
                    for line in product['lines']:
                        text_format = fmt_text_bold if line['is_last'] else fmt_text
                        qty_format = fmt_qty_bold if line['is_last'] else fmt_qty
                        money_format = fmt_money_bold if line['is_last'] else fmt_money

                        col = 0
                        worksheet.write_number(row, col, line['nro'], text_format); col += 1
                        worksheet.write(row, col, line['date'], text_format); col += 1
                        worksheet.write(row, col, line['category_name'], text_format); col += 1
                        if data['show_concept']:
                            worksheet.write(row, col, line['concept'], text_format); col += 1
                        if data['show_locations']:
                            worksheet.write(row, col, line['origin'], text_format); col += 1
                            worksheet.write(row, col, line['dest'], text_format); col += 1
                        if data['show_document']:
                            worksheet.write(row, col, line['document'], text_format); col += 1
                        worksheet.write(row, col, line['product_name'], text_format); col += 1
                        for uom_value in line['uom_values']:
                            if uom_value is None:
                                worksheet.write_blank(row, col, None, qty_format)
                            else:
                                worksheet.write_number(row, col, uom_value, qty_format)
                            col += 1

                        if data['details']:
                            values = [
                                (line['entry_qty'], qty_format),
                                (line['entry_unit'], money_format),
                                (line['entry_total'], money_format),
                                (line['output_qty'], qty_format),
                                (line['output_unit'], money_format),
                                (line['output_total'], money_format),
                                (line['balance_qty'], qty_format),
                                (line['balance_unit'], money_format),
                                (line['balance_total'], money_format),
                            ]
                        else:
                            values = [
                                (line['balance_qty'], qty_format),
                                (line['balance_unit'], money_format),
                                (line['balance_total'], money_format),
                            ]
                        for value, cell_format in values:
                            worksheet.write_number(row, col, value or 0.0, cell_format)
                            col += 1
                        row += 1

                if data['group_categories']:
                    worksheet.merge_range(row, 0, row, finance_start - 1, 'TOTAL CATEGORÍA %s' % category['name'], fmt_total_label)
                    if data['details']:
                        for col in range(finance_start, finance_start + 8):
                            worksheet.write_blank(row, col, None, fmt_money_bold)
                        worksheet.write_number(row, finance_start + 8, category['total_value'], fmt_money_bold)
                    else:
                        worksheet.write_blank(row, finance_start, None, fmt_money_bold)
                        worksheet.write_blank(row, finance_start + 1, None, fmt_money_bold)
                        worksheet.write_number(row, finance_start + 2, category['total_value'], fmt_money_bold)
                    row += 1

            if data['group_warehouses']:
                worksheet.merge_range(row, 0, row, finance_start - 1, 'TOTAL ALMACÉN %s' % section['name'], fmt_total_label)
                if data['details']:
                    for col in range(finance_start, finance_start + 8):
                        worksheet.write_blank(row, col, None, fmt_money_bold)
                    worksheet.write_number(row, finance_start + 8, section['total_value'], fmt_money_bold)
                else:
                    worksheet.write_blank(row, finance_start, None, fmt_money_bold)
                    worksheet.write_blank(row, finance_start + 1, None, fmt_money_bold)
                    worksheet.write_number(row, finance_start + 2, section['total_value'], fmt_money_bold)
                row += 1

        if finance_start > 0:
            worksheet.merge_range(row, 0, row, finance_start - 1, 'TOTAL GENERAL', fmt_total_label)
        if data['details']:
            for col in range(finance_start, finance_start + 8):
                worksheet.write_blank(row, col, None, fmt_money_bold)
            worksheet.write_number(row, finance_start + 8, data['total_value'], fmt_money_bold)
        else:
            worksheet.write_blank(row, finance_start, None, fmt_money_bold)
            worksheet.write_blank(row, finance_start + 1, None, fmt_money_bold)
            worksheet.write_number(row, finance_start + 2, data['total_value'], fmt_money_bold)

        worksheet.freeze_panes(header_row + 2, 0)
        worksheet.set_landscape()
        worksheet.fit_to_pages(1, 0)
        worksheet.repeat_rows(header_row, header_row + 1)
        worksheet.set_margins(0.25, 0.25, 0.45, 0.45)

        workbook.close()
        output.seek(0)
        return output.read(), self._excel_filename()

    # Compatibilidad con código externo que todavía llame al método antiguo.
    def _imprimir_xls_reporte_kardex(self):
        return self.action_report_kardex()

    # Compatibilidad con referencias antiguas del módulo.
    def return_value_promedio_transferencias_internas(self, product_id, date):
        product = self.env['product.product'].browse(product_id)
        return self._historical_transfer_unit_cost(product, date)

    def name_ubicacion(self, nombre_almacen):
        warehouse = self.env['stock.warehouse'].search([('name', '=', nombre_almacen)], limit=1)
        return warehouse.lot_stock_id.display_name if warehouse else nombre_almacen
