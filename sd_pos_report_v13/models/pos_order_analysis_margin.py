# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    # ESI corrección: cantidad normalizada a la UDM base del producto.
    # Cuando pos_multi_uom está instalado, line.qty representa la cantidad de la
    # UDM elegida (por ejemplo 2 Cajas), no necesariamente unidades de inventario.
    # Guardamos también la cantidad equivalente en la UDM base (por ejemplo 48
    # Unidades) para que Análisis de pedidos y los costos sean matemáticamente correctos.
    esi_base_qty = fields.Float(
        string='Cantidad base ESI',
        compute='_compute_esi_uom_metrics',
        store=True,
        readonly=True,
        digits='Product Unit of Measure',
        help='Cantidad convertida a la unidad de medida base del producto.',
    )

    # ESI corrección: el costo del producto está expresado por su UDM base.
    # Por tanto el costo correcto es cantidad base x standard_price, no qty x costo
    # cuando la venta se hizo en Caja, Paquete, Docena, etc.
    esi_cost_total = fields.Float(
        string='Costo estimado',
        compute='_compute_esi_uom_metrics',
        store=True,
        readonly=True,
        digits='Product Price',
        help=(
            'Costo estimado calculado con la cantidad convertida a la unidad '
            'base del producto. Compatible con ventas realizadas mediante '
            'pos_multi_uom.'
        ),
    )

    def _esi_get_base_qty(self):
        """Return line qty converted from selected POS UOM to product base UOM."""
        self.ensure_one()
        qty = self.qty or 0.0
        if not self.product_id or not qty:
            return qty

        base_uom = self.product_id.uom_id

        # ESI corrección: compatibilidad opcional; sd_pos_report_v13 no obliga a
        # instalar pos_multi_uom. Si el campo existe, respetamos la UDM guardada
        # en la línea; si no existe o está vacío usamos la UDM base normal de Odoo.
        selected_uom = base_uom
        if 'product_uom' in self._fields and self.product_uom:
            selected_uom = self.product_uom

        if (
            not selected_uom
            or not base_uom
            or selected_uom.category_id != base_uom.category_id
        ):
            return qty

        # round=False evita alterar cantidades al calcular costo/análisis. El
        # movimiento de stock puede redondear según su UDM, pero aquí necesitamos
        # mantener la equivalencia matemática exacta para el reporte.
        return selected_uom._compute_quantity(qty, base_uom, round=False)

    @api.depends('qty', 'product_id', 'order_id.company_id')
    def _compute_esi_uom_metrics(self):
        for line in self:
            base_qty = line._esi_get_base_qty() if line.product_id else 0.0
            line.esi_base_qty = base_qty

            if not line.product_id or not base_qty:
                line.esi_cost_total = 0.0
                continue

            company = line.order_id.company_id or self.env.company
            product = line.product_id.sudo().with_context(force_company=company.id)
            unit_cost = product.standard_price or 0.0
            line.esi_cost_total = base_qty * unit_cost

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(PosOrderLine, self).create(vals_list)
        # ESI corrección: product_uom pertenece a pos_multi_uom y por eso no puede
        # declararse directamente en @api.depends sin convertir este módulo en una
        # dependencia obligatoria. Forzamos el cálculo después de crear para tomar
        # la UDM elegida incluso cuando es un campo opcional.
        if 'product_uom' in self._fields:
            lines._compute_esi_uom_metrics()
        return lines

    def write(self, vals):
        result = super(PosOrderLine, self).write(vals)
        # ESI corrección: si alguien modifica la UDM desde la orden POS, recalcular
        # cantidad base y costo aunque product_uom sea un campo de otro módulo.
        if 'product_uom' in vals and 'product_uom' in self._fields:
            self._compute_esi_uom_metrics()
        return result


class PosOrderReport(models.Model):
    _inherit = 'report.pos.order'

    # ESI corrección: medidas monetarias del análisis POS.
    esi_cost_total = fields.Float(
        string='Costo estimado',
        readonly=True,
        help=(
            'Costo estimado según la cantidad real expresada en la unidad base '
            'del producto. Si se venden 2 cajas de 24, el costo se calcula sobre '
            '48 unidades.'
        ),
    )
    esi_profit_estimated = fields.Float(
        string='Ganancia estimada',
        readonly=True,
        help='Precio total menos costo estimado.',
    )

    def _select(self):
        # ESI corrección: Odoo 13 usa SUM(l.qty) para "Cantidad del producto".
        # Con pos_multi_uom l.qty puede ser 2 Cajas, mientras inventario recibe 48
        # Unidades. Sustituimos solamente esa medida por la cantidad base guardada;
        # el resto de la consulta nativa se conserva intacto.
        native_select = super(PosOrderReport, self)._select()
        native_select = native_select.replace(
            'SUM(l.qty) AS product_qty',
            'SUM(COALESCE(l.esi_base_qty, l.qty)) AS product_qty'
        )

        # Precio total conserva exactamente la fórmula nativa de Odoo 13.
        price_total_sql = """
            SUM(ROUND(
                (l.qty * l.price_unit) * (100 - l.discount) / 100
                / CASE COALESCE(s.currency_rate, 0)
                    WHEN 0 THEN 1.0 ELSE s.currency_rate END,
                cu.decimal_places
            ))
        """
        return native_select + """,
            SUM(COALESCE(l.esi_cost_total, 0.0)) AS esi_cost_total,
            (%s - SUM(COALESCE(l.esi_cost_total, 0.0))) AS esi_profit_estimated
        """ % price_total_sql
