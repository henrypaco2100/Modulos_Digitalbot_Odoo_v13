# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from itertools import groupby
from ..models import inherit_stock_move

_logger = logging.getLogger(__name__)


class saldoReport(models.TransientModel):
    _name = 'saldo.producto'

    @api.model
    def default_get(self, fields):
        res = super(saldoReport, self).default_get(fields)
        stock_move_line_id = self.env.context.get('default_id') or self.env.context.get('active_id')
        if stock_move_line_id:
            stock_move_line_id = self.env['stock.move.line'].browse(stock_move_line_id)
        if stock_move_line_id.exists():
            stock_move_line_id.ensure_one()
            if 'stock_move_line_id' in fields:
                res['stock_move_line_id'] = stock_move_line_id.id
            if 'company_id' in fields:
                res['company_id'] = stock_move_line_id.company_id.id
            if 'product_id' in fields:
                res['product_id'] = stock_move_line_id.product_id.id
            if 'name' in fields:
                res['name'] = stock_move_line_id.product_id.name
            if 'sd_date_end' in fields:
                res['sd_date_end'] = stock_move_line_id.date or stock_move_line_id.move_id.date
            if 'currency_id' in fields:
                res['currency_id'] = stock_move_line_id.currency_id.id
        return res



    name = fields.Char(string="Nombre")
    company_id = fields.Many2one('res.company', string='Compañia')
    currency_id = fields.Many2one('res.currency', string='Divisa')
    product_id = fields.Many2one('product.product', string='producto')
    stock_move_line_id = fields.Many2one('stock.move.line')
    sd_stock_warehouse_ids = fields.Many2many('stock.warehouse', string="Almacen")
    sd_stock_location_ids = fields.Many2many('stock.location', string="Ubicacion", domain=lambda self: [('id', 'in', self.get_location_ids())])
    sd_date_start = fields.Datetime(string="Fecha inicio", required=False)
    sd_date_end = fields.Datetime(string="Fecha fin", readonly=True)
    sd_is_lote = fields.Boolean(string="Por lote", default=False)
    # sd_cantidad = fields.Integer(string="cantidad", compute="_compute_saldo", store=False)
    sd_saldo_producto_line_ids = fields.One2many('saldo.producto.line', 'sd_saldo_producto_id', string='Saldo Producto Linea')

    @api.model
    # funcion que retorna las localizaciones de los almacenes seleccionados en sd_stockwarehouse_ids
    def get_location_ids(self):
        print('entrando al domain')
        array_location_ids = []
        for almacen in self.sd_stock_warehouse_ids:
            location_almacen_ids = self.get_array_location(almacen)
            # location_ids = self.env['stock.location'].search([('id', 'in', location_almacen_ids), ('usage', '=', 'internal')])
            for location in location_almacen_ids:
                array_location_ids.append(location.id)
        print('array_location_ids: ', array_location_ids)
        return array_location_ids

    def cargar_tabla(self):
        self.consulta_saldo()
        return{
            'name': 'Saldo de producto hasta la fecha',
            'view_mode': 'form',
            'view_id': False,
            'res_model': self._name,
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }


    #FUNCION QUE CALCULA LA CANTIDAD, VR UNITARIO Y SALDO TOTAL DEL PRODUCTO HASTA LA FECHA
    def consulta_saldo(self):
        array_locations = []
        simulacion_movimientos = {
            'cantidad': 0,
            'total': 0,
            'remaining': 0
        }
        locations = self.env['stock.location'].search([('usage', '=', 'internal')])
        #ESTE CODIGO ES PARA FILTRAR UBICACIONES Y ALMACENES, LUEGO BORRAR LA ASIGNACION (ARRAY_LOCATIONS = LOCATIONS)
        # for location in locations:
        #     if self.get_warehouse_id(location) in self.sd_stock_warehouse_ids:
        #         array_locations.append(location)
        # for location in self.sd_stock_location_ids:
        #     if location not in array_locations:
        #         array_locations.append(location)
        array_locations = locations
        if self.sd_date_start:
            stock_move_ids = self.env['stock.move.line'].search(
                [('state', '=', 'done'), ('product_id', '=', self.product_id.id),
                 ('date', '<=', self.sd_date_end),
                 ('date', '>=', self.sd_date_start)], order='date asc')
        else:
            stock_move_ids = self.env['stock.move.line'].search(
                [('state', '=', 'done'), ('product_id', '=', self.product_id.id),
                 ('date', '<=', self.sd_date_end)], order='date asc')
        array_movimientos = []
        total = 0
        cantidad = 0
        costo_unit = 0
        for movimiento in stock_move_ids:
            if not self.sd_is_lote or (self.sd_is_lote and self.stock_move_line_id.lot_id == movimiento.lot_id):
                if movimiento.location_id in array_locations or movimiento.location_dest_id in array_locations:
                    switcher = {
                        'supplier_internal': 'Compra',
                        'internal_customer': 'Venta',
                        'internal_inventory': 'Ajuste de Inventario Salida',
                        # DESCOMENTAR PARA FILTRAR POR ALMACENES Y UBICACIONES
                        # 'internal_internal': 'Transferencia Interna',
                        'inventory_internal': 'Ajuste de Inventario Entrada'
                    }
                    tipo = switcher.get(movimiento.location_id.usage + '_' + movimiento.location_dest_id.usage, 'No definido')
                    array_movimientos.append(movimiento)
                    if tipo in ['Compra', 'Ajuste de Inventario Entrada']:
                        cantidad += abs(movimiento.qty_done)
                        total += abs(movimiento.cost_valuation_total)
                    if tipo in ['Venta', 'Ajuste de Inventario Salida']:
                        cantidad -= abs(movimiento.qty_done)
                        total -= abs(movimiento.cost_valuation_total)
                    if tipo == 'Transferencia Interna':
                        array_purchases = self.env['sale.order'].search(['state', '=', 'done'])
                        locationorigen = movimiento.location_id
                        locationdestino = movimiento.location_dest_id
                        if locationorigen in array_locations and locationdestino not in array_locations:
                            cantidad -= abs(movimiento.qty_done)
                            #total -= abs(movimiento.cost_valuation_total)
                            if movimiento.product_id.categ_id.property_cost_method == 'average':
                                total = total - (total / cantidad)
                            # if movimiento.product_id.categ_id.property_cost_method == 'standard':
                            #     total = total - (total / cantidad)
                        if locationorigen not in array_locations and locationdestino in array_locations:
                            cantidad += abs(movimiento.qty_done)
                            #total += abs(movimiento.cost_valuation_total)
                            if movimiento.product_id.categ_id.property_cost_method == 'average':
                                total = total + (total / cantidad)
                            # if movimiento.product_id.categ_id.property_cost_method == 'standard':
                            #     total = total - (total / cantidad)
                    # print('producto: ', movimiento.product_id.name, ' - ', tipo,' - cant: ', cantidad,' - vr unit: ', total/cantidad, ' - total: ', total)
                    if self.sd_is_lote: print('lote: ', movimiento.lot_id.name)

        if cantidad > 0: costo_unit = total/cantidad
        if not self.sd_saldo_producto_line_ids:
            val = {
                'name': self.name,
                'sd_cantidad': cantidad,
                'sd_costo_unit': costo_unit,
                'sd_saldo': total,
                'sd_saldo_producto_id': self.id

            }
            self.env['saldo.producto.line'].create(val)
        else:
            for saldo_producto_id in self.sd_saldo_producto_line_ids:
                saldo_producto_id.update({
                    'name': self.name,
                    'sd_cantidad': cantidad,
                    'sd_costo_unit': total / cantidad,
                    'sd_saldo': total
                })
        # return stock_move_ids

    def get_warehouse_id(self, ubicacion_id):

        ubicacion_padre = self.get_padre_principal(ubicacion_id)
        #print('id padre: ', ubicacion_padre)
        warehouse_id = self.env['stock.warehouse'].search(
            [('lot_stock_id', '=', ubicacion_padre)])
        return warehouse_id

    def get_padre_principal(self, ubicacion_id):
        if ubicacion_id.location_id.usage == "view":
            #print('ubicacion padre: ', ubicacion_id.name, self.reference, ubicacion_id.id)
            return ubicacion_id.id
        if ubicacion_id.location_id:
            return self.get_padre_principal(ubicacion_id.location_id)
        else:
            return ubicacion_id.id

    def get_array_location(self, almacen):
        array_locations = []
        print('almacen: ', almacen)
        if almacen:
            total_locations = self.env['stock.location'].search([('usage', '=', 'internal')])
            for location in total_locations:
                if self.get_warehouse_id(location) == almacen:
                    array_locations.append(location)
            print('array locations: ', array_locations)
        return array_locations

    @api.onchange('stock_move_line_id')
    def cargar_datos(self):
        print('quien yo?')
        switcher = {
            'supplier_internal': 'Compra',
            'internal_customer': 'Venta',
            'internal_inventory': 'Ajuste de inventario de salida',
            'internal_internal': 'Transferencia interna',
            'inventory_internal': 'Ajuste de Inventario Entrada',
            'production_internal': 'Produccion para almacen',
            'internal_production': 'Materia prima para produccion'
        }
        tipo = switcher.get(self.stock_move_line_id.location_id.usage + '_' + self.stock_move_line_id.location_dest_id.usage,
                            'No definido')
        if self.stock_move_line_id.lot_id.name:
            self.name += ' - ' + self.stock_move_line_id.lot_id.name
            self.write({'sd_is_lote': True})


        if tipo in ['Compra', 'Transferencia interna', 'Ajuste de Inventario Entrada', 'Produccion para almacen']:
            self.write({
                'sd_stock_location_ids': [self.stock_move_line_id.location_dest_id.id],
                'sd_stock_warehouse_ids': [self.stock_move_line_id.move_id.get_warehouse_id(self.stock_move_line_id.location_dest_id).id]
            })
        else:
            self.write({
                'sd_stock_location_ids': [self.stock_move_line_id.location_id.id],
                'sd_stock_warehouse_ids': [self.stock_move_line_id.move_id.get_warehouse_id(self.stock_move_line_id.location_id).id]
            })
        self.consulta_saldo()
        print('si, tu!')

    @api.onchange('sd_is_lote')
    def not_change_lote(self):
        if not self.stock_move_line_id.lot_id:
            self.sd_is_lote = False


class saldoReportLine(models.TransientModel):
    _name = 'saldo.producto.line'
    name = fields.Char(string='Nombre')
    sd_saldo_producto_id = fields.Many2one('saldo.producto', string='saldo producto')
    sd_cantidad = fields.Float(string='Cantidad')
    sd_costo_unit = fields.Float(string='Costo Unitario')
    sd_saldo = fields.Float(string='Saldo')
