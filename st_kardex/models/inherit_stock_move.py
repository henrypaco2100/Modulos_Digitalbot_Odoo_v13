from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SdInheritStockMoveKardex2(models.Model):
    _inherit = 'stock.move'
    sd_almacen_origen = fields.Many2one('stock.warehouse', string='Almacen Origen')
    sd_almacen_destino = fields.Many2one('stock.warehouse', string='Almacen Destino')

    @api.onchange('location_id')
    def cambio_origen(self):
        self.sd_almacen_origen = self.get_warehouse_id(self.location_id)

    @api.onchange('location_dest_id')
    def cambio_destino(self):
        self.sd_almacen_destino = self.get_warehouse_id(self.location_dest_id)

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

    def rellenar_almacenes(self):
        query = """
        WITH RECURSIVE padres AS (
            SELECT 
                id,
                name,
                location_id,
                id AS root_id,
                name AS root_name
            FROM 
                stock_location
            WHERE 
                usage = 'view'
            UNION ALL
            SELECT 
                sl.id,
                sl.name,
                sl.location_id,
                p.root_id,
                p.root_name
            FROM 
                stock_location sl
            JOIN 
                padres p ON sl.location_id = p.id
        ),
        ubicaciones_padres AS (
            SELECT 
                sl.id AS ubicacion_id,
                p.root_id AS padre_principal_id
            FROM 
                stock_location sl
            LEFT JOIN 
                padres p ON sl.id = p.id
        ),
        almacenes_origen AS (
            SELECT 
                sm.id AS stock_move_id,
                sw.id AS warehouse_id
            FROM 
                stock_move sm
            JOIN 
                ubicaciones_padres up ON sm.location_id = up.ubicacion_id
            JOIN 
                stock_warehouse sw ON up.padre_principal_id = sw.lot_stock_id
            WHERE 
                sm.state = 'done'
        ),
        almacenes_destino AS (
            SELECT 
                sm.id AS stock_move_id,
                sw.id AS warehouse_id
            FROM 
                stock_move sm
            JOIN 
                ubicaciones_padres up ON sm.location_dest_id = up.ubicacion_id
            JOIN 
                stock_warehouse sw ON up.padre_principal_id = sw.lot_stock_id
            WHERE 
                sm.state = 'done'
        )
        UPDATE stock_move
        SET sd_almacen_origen = ao.warehouse_id,
            sd_almacen_destino = ad.warehouse_id
        FROM almacenes_origen ao, almacenes_destino ad
        WHERE stock_move.id = ao.stock_move_id AND stock_move.id = ad.stock_move_id;
        """
        self.env.cr.execute(query)

    # RELLENAR LUIS
    # def rellenar_almacenes(self):
    #     stock_move_ids = self.env['stock.move'].search([('state', '=', 'done')])
    #     for stock_move in stock_move_ids:
    #         stock_move.write({'sd_almacen_origen': stock_move.get_warehouse_id(stock_move.location_id)})
    #         stock_move.write({'sd_almacen_destino': stock_move.get_warehouse_id(stock_move.location_dest_id)})

    @api.model_create_multi
    def create(self, vals):
        records = super(SdInheritStockMoveKardex2, self).create(vals)
        for record in records:
            almacen_origen = self.get_warehouse_id(record.location_id)
            almacen_destino = self.get_warehouse_id(record.location_dest_id)
            record.sd_almacen_origen = almacen_origen
            record.sd_almacen_destino = almacen_destino
        return records
