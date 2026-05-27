import logging
from odoo import fields, models, api, _

class CargarTipoMovimientos(models.Model):
    _name = "cargar.movimientos"

    def action_load_move_types(self):
        for stock_move_line_id in self:
            if not stock_move_line_id.type_id:
                location_id = stock_move_line_id.location_id.usage
                location_dest_id = stock_move_line_id.location_dest_id.usage
                almacen_origen = str(
                    stock_move_line_id.move_id.get_warehouse_id(stock_move_line_id.location_id).display_name)
                almacen_destino = str(
                    stock_move_line_id.move_id.get_warehouse_id(stock_move_line_id.location_dest_id).display_name)
                if almacen_destino and almacen_origen:
                    switcher = {
                        'supplier_internal': 'Compra - ' + almacen_destino,
                        'internal_customer': 'Venta - ' + almacen_origen,
                        'internal_inventory': 'Ajuste de inventario de salida',
                        'internal_internal': 'Trans. Int. de ' + almacen_origen + ' a ' + almacen_destino,
                        'inventory_internal': 'Ajuste de Inventario Entrada'
                    }
                    tipo = switcher.get(location_id + '_' + location_dest_id, 'No definido')
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
