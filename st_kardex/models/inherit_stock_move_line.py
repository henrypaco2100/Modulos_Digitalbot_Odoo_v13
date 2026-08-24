from odoo import fields, models, api, _
from . import inherit_stock_move
#DAVID MODELO HEREDADO PARA PODER AGREGAR MAS CAMPOS A LA VISTA DE MOVIMIENTO DE PRODUCTOS
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    currency_id = fields.Many2one('res.currency', 'Currency', related='company_id.currency_id', readonly=True,
                                 required=True)

    cost_valuation_total = fields.Monetary(string="Valoracion Total", compute='_get_valoracion', store=True)
    # cost_valuation_total = fields.Monetary(string="Valoracion Total", default=0.0, compute='_compute_valuation_total', readonly=True, store=False)

    cost_valuation = fields.Monetary(string="Valoracion Unitario", readonly=True, compute='_get_valoracion', store=True)
    costo_dest = fields.Monetary(string="Valoracion Dest. Unit.", readonly=True)
    costo_dest_total = fields.Monetary(string="Valoracion Dest. Tot.", readonly=True)

    landed_cost_unit = fields.Float(string="Nuevo Costo LC",
                                    help="Este campo muestra si se tiene un costo nuevo en base a los landed cost")

    landed_cost_saldo = fields.Float(string="Cost Landed Saldo")

    type_id = fields.Char(readonly=True, compute='_get_default_type_move', store=False)
    sd_type = fields.Char(string='tipo char', readonly=True)
    # sd_qty = fields.Float(string='Cantidad',compute='_get_valoracion', store=True)
    #ids_model_types = fields.Many2one('move.types')
    # MEJORAS CHATGPT
    # @api.depends('move_id.stock_valuation_layer_ids')
    # def _get_valoracion(self):
    #     for stock_move_line_id in self:
    #         stock_move_line_id.cost_valuation_total = 0
    #         stock_move_line_id.cost_valuation = 0
    #         stock_move_line_id.costo_dest = 0
    #         stock_move_line_id.costo_dest_total = 0
    #
    #         # Sumar los valores de stock_valuation_layer_ids para calcular costo_total_move y costo_dest_total
    #         self.env.cr.execute("""
    #                 SELECT
    #                     COALESCE(SUM(value), 0) AS costo_total_move,
    #                     COALESCE(SUM(CASE WHEN stock_landed_cost_id IS NOT NULL THEN value ELSE 0 END), 0) AS costo_dest_total
    #                 FROM
    #                     stock_valuation_layer
    #                 WHERE
    #                     move_id = %s
    #             """, (stock_move_line_id.move_id.id,))
    #         result = self.env.cr.fetchone()
    #         costo_total_move = result[0]
    #         stock_move_line_id.costo_dest_total = result[1]
    #
    #         # Calcular cost_valuation y otras cantidades
    #         if stock_move_line_id.move_id.quantity_done != 0:
    #             stock_move_line_id.cost_valuation = abs(
    #                 costo_total_move / stock_move_line_id.move_id.quantity_done) if costo_total_move != 0 else 0
    #             stock_move_line_id.cost_valuation_total = stock_move_line_id.qty_done * (
    #                         costo_total_move / stock_move_line_id.move_id.quantity_done) if costo_total_move != 0 else 0
    #             stock_move_line_id.sd_qty = stock_move_line_id.qty_done * (
    #                         costo_total_move / abs(costo_total_move)) if costo_total_move != 0 else 0
    #             stock_move_line_id.costo_dest = stock_move_line_id.costo_dest_total / stock_move_line_id.move_id.quantity_done if stock_move_line_id.costo_dest_total != 0 else 0
    #         else:
    #             stock_move_line_id.cost_valuation = 0
    #             stock_move_line_id.costo_dest = 0

    # HENRY CODIGO
    @api.depends('move_id.stock_valuation_layer_ids')
    def _get_valoracion(self):
        for stock_move_line_id in self:
            stock_move_line_id.cost_valuation_total = 0
            stock_move_line_id.cost_valuation = 0
            stock_move_line_id.costo_dest = 0
            stock_move_line_id.costo_dest_total = 0
            costo_total_move = 0
            cantidad = 0
            for stock_valuation_layer_id in stock_move_line_id.move_id.stock_valuation_layer_ids:
                if hasattr(stock_valuation_layer_id,'stock_landed_cost_id'):
                    if stock_valuation_layer_id.stock_landed_cost_id:
                        stock_move_line_id.costo_dest_total += stock_valuation_layer_id.value
                costo_total_move += stock_valuation_layer_id.value
            if stock_move_line_id.move_id.quantity_done!= 0:
                stock_move_line_id.cost_valuation = abs(costo_total_move / stock_move_line_id.move_id.quantity_done if costo_total_move != 0 else 0)
                stock_move_line_id.cost_valuation_total = stock_move_line_id.qty_done * (costo_total_move / stock_move_line_id.move_id.quantity_done if costo_total_move != 0 else 0)
                # stock_move_line_id.sd_qty =  stock_move_line_id.qty_done * (costo_total_move /abs(costo_total_move)) if costo_total_move != 0 else 0
                # PARA CORTEAR IMPORTACION HENRY
                stock_move_line_id.costo_dest = stock_move_line_id.costo_dest_total / stock_move_line_id.move_id.quantity_done if stock_move_line_id.costo_dest_total != 0 else 0
            else:
                stock_move_line_id.cost_valuation = 0
                stock_move_line_id.costo_dest = 0


    @api.depends('location_dest_id', 'location_id')
    def _get_default_type_move(self):
        for stock_move_line_id in self:
            location_id = stock_move_line_id.location_id.usage
            location_dest_id = stock_move_line_id.location_dest_id.usage
            almacen_origen = str(stock_move_line_id.move_id.get_warehouse_id(stock_move_line_id.location_id).display_name)
            almacen_destino = str(stock_move_line_id.move_id.get_warehouse_id(stock_move_line_id.location_dest_id).display_name)
            if almacen_destino and almacen_origen:
                switcher = {
                    'supplier_internal':'Compra - ' + almacen_destino,
                    'internal_customer': 'Venta - ' + almacen_origen,
                    'internal_inventory': 'Ajuste de inventario de salida',
                    'internal_internal': 'Trans. Int. de ' + almacen_origen + ' a ' + almacen_destino,
                    'inventory_internal': 'Ajuste de Inventario Entrada'
                }
                tipo = switcher.get(location_id+'_'+location_dest_id, 'No definido')
            else:
                switcher = {
                    'supplier_internal': 'Compra',
                    'internal_customer': 'Venta',
                    'internal_inventory': 'Ajuste de inventario de salida',
                    'internal_internal': 'Trans. Int.',
                    'inventory_internal': 'Ajuste de Inventario Entrada'
                }
                tipo = switcher.get(location_id + '_' + location_dest_id, 'No definido')

            stock_move_line_id.type_id = tipo
            stock_move_line_id.update({
                'sd_type': tipo
            })

    def action_wizard_saldo(self):
        self.ensure_one()
        action = self.env.ref('st_kardex.sd_action_saldo_producto').read()[0]
        return action

    # @api.model
    # def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
    #     res = super(StockMoveLine, self).read_group(domain, fields, groupby, offset=offset,
    #                                                                       limit=limit, orderby=orderby,
    #                                                                       lazy=lazy)
    #     if 'cost_valuation_total' in fields:
    #         for line in res:
    #             if '__domain' in line:
    #                 lines = self.search(line['__domain'])
    #                 total_saldo = 0.0
    #                 for record in lines:
    #                     total_saldo += abs(record.cost_valuation_total)
    #                 line['cost_valuation_total'] = total_saldo
    #
    #     return res

