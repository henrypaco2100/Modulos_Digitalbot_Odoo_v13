from odoo import api, fields, models, tools,_
from odoo.exceptions import AccessError, UserError, ValidationError
from ast import literal_eval
class InheritMrpProduction(models.Model):
    _inherit = 'mrp.production'
    sd_autor_2_id = fields.Many2one('res.partner', string='Autor 2')
    sd_autor_id = fields.Many2one('res.partner', string='Autor')
    sd_client_id = fields.Many2one('res.partner', string='Cliente')
    sd_correccion_id = fields.Many2one('res.partner', string='Correccion')
    sd_diagramacion_id = fields.Many2one('res.partner', string='Diagramacion')
    sd_tapa_id = fields.Many2one('res.partner', string='Tapa')

    sd_cotizacion = fields.Boolean(string='Cotizacion')
    sd_contrato = fields.Boolean(string='Contrato')

    sd_ISBN = fields.Char(string='ISBN', related='product_id.barcode',readonly=False,store=True)
    sd_nit = fields.Char(string='Nit')
    sd_formato = fields.Char(string='Formato',related='product_id.sd_formato', readonly=False,store=True)

    sd_paginas_bn = fields.Integer(string='Negro')
    sd_paginas_color = fields.Integer(string='Color')
    sd_paginas_otro = fields.Integer(string='Otro')
    sd_paginas_total = fields.Integer(string='Paginas', compute='_compute_paginas_total', store=True)
    sd_nota = fields.Text(string='Nota')
    sd_total_costo = fields.Monetary(compute='_compute_costo_total_producto_terminado',string='Costo total',store=True)
    currency_id = fields.Many2one('res.currency', string='Moneda',default=lambda self: self.env.company.currency_id.id)
    sd_account_analitica_out = fields.Many2one('account.analytic.account',string='Cuenta analitica de Proceso')
    sd_costo_previsto = fields.Monetary(compute='_compute_costo_total_producto_previsto',string='Costo Previsto',store=True)
    sd_extras_move_ids = fields.One2many('stock.move','sd_material_extra_production_id',string='Componentes Extras',copy=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        domain=[('scrapped', '=', False)])
    sd_componentes_extras = fields.Boolean(string='Componentes Extras',default=True)
    sd_category_product_id = fields.Many2one(related='product_id.categ_id',string='Categoria',store=True)
    sd_imagen = fields.Image(string='Imagen',related='product_id.image_1920')
    sd_tipo_impresion = fields.Selection([
        ('offset', 'Offset'),
        ('digital', 'Digital'),],
        string='Tipo de Impresión')
    @api.onchange('sd_autor_id')
    def _compute_sd_autor_id(self):
        for record in self:
            record.sd_autor = record.sd_autor_id.name

    @api.onchange('sd_client_id')
    def _compute_sd_client_id(self):
        for record in self:
            record.sd_nit = record.sd_client_id.vat

    @api.depends('sd_paginas_color', 'sd_paginas_bn','sd_paginas_otro')
    def _compute_paginas_total(self):
        for record in self:
            record.sd_paginas_total = record.sd_paginas_color + record.sd_paginas_bn + record.sd_paginas_otro
        
    # MRP PARA MOSTRAR EL COSTO TOTAL- HENRY
    @api.depends('move_raw_ids.sd_valuation','sd_componentes_extras','sd_extras_move_ids.sd_valuation')
    def _compute_costo_total_producto_terminado(self):
        for record in self:
            total_costo = 0
            for move_raw in record.move_raw_ids:
                total_costo += move_raw.sd_valuation
            if record.sd_componentes_extras:
                for extras_move in record.sd_extras_move_ids:
                    total_costo += extras_move.sd_valuation
            record.write({
                'sd_total_costo': abs(total_costo),
            })

    @api.depends('move_raw_ids.sd_total_precio','sd_componentes_extras','sd_extras_move_ids.sd_total_precio')
    def _compute_costo_total_producto_previsto(self):
        for record in self:
            total_costo = 0
            for move_raw in record.move_raw_ids:
                total_costo += move_raw.sd_total_precio
            if record.sd_componentes_extras:
                for extras_move in record.sd_extras_move_ids:
                    total_costo += extras_move.sd_total_precio
            record.write({
                'sd_costo_previsto': abs(total_costo),
            })

    # def button_mark_done(self):
    #     # adicionar servicio extras a produccion - Henry
    #     for move_raw in self.move_raw_ids.filtered(lambda x: x.sd_precio_servicio != 0):
    #         move_raw.product_id.sudo().write({
    #             'standard_price':move_raw.sd_precio_servicio
    #         })
    #     res = super().button_mark_done()
    #     return res

    # CODIGO PARA COMPONENTES EXTRAS - HENRY
    @api.onchange('company_id')
    def onchange_company_id(self):
        super(InheritMrpProduction, self).onchange_company_id()
        if self.company_id:
            if self.sd_extras_move_ids:
                self.sd_extras_move_ids.update({'company_id': self.company_id})

    @api.onchange('date_planned_start')
    def _onchange_date_planned_start(self):
        super(InheritMrpProduction, self)._onchange_date_planned_start()
        self.sd_extras_move_ids.update({
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
        })

    @api.onchange('location_src_id', 'move_raw_ids', 'routing_id','sd_extras_move_ids')
    def _onchange_location(self):
        super(InheritMrpProduction, self)._onchange_location()
        source_location = self.location_src_id
        self.sd_extras_move_ids.update({
            'warehouse_id': source_location.get_warehouse().id,
            'location_id': source_location.id,
        })

    @api.onchange('picking_type_id')
    def onchange_picking_type(self):
        super(InheritMrpProduction, self).onchange_picking_type()
        self.sd_extras_move_ids.update({'picking_type_id': self.picking_type_id})

    @api.constrains('product_id', 'move_raw_ids')
    def _check_production_lines(self):
        super(InheritMrpProduction, self)._check_production_lines()
        for production in self:
            for move in production.sd_extras_move_ids:
                if production.product_id == move.product_id:
                    raise ValidationError(
                        _("El componente %s no debe ser el mismo que el producto a producir.") % production.product_id.display_name)
    def action_confirm(self):
        self._check_company()
        res = super(InheritMrpProduction, self).action_confirm()
        for production in self:
            # Avoid confirming it twice
            for move_raw in production.sd_extras_move_ids:
                move_raw.write({
                    'unit_factor': move_raw.product_uom_qty / production.product_qty,
                })
            production.sd_extras_move_ids._adjust_procure_method()
            production.sd_extras_move_ids._action_confirm()
        return res
    def action_cambiar_precio_unitario_product_service(self):
        for move in self.move_raw_ids:
            if move.product_id.categ_id.property_cost_method=='standard':
                move.product_id.sudo().update({
                    'standard_price': move.sd_precio_unitario,
                })
                move.sudo().update({
                     'price_unit': move.sd_precio_unitario,
                })
            # move.sudo().update({
            #     'picking_type_id':move.raw_material_production_id.picking_type_id,
            #     'price_unit': move.sd_precio_unitario,
            #     'availability':move.product_uom_qty,
            #     'location_dest_id':move.raw_material_production_id.production_location_id,
            #     'sd_almacen_destino':None,
            #     'warehouse_id': move.raw_material_production_id.location_src_id.get_warehouse().id,
            #     'display_name':'Stock>My Company: Production',
            #
            # })
        for move in self.sd_extras_move_ids:
            if move.product_id.categ_id.property_cost_method=='standard':
                move.product_id.sudo().update({
                    'standard_price': move.sd_precio_unitario,
                })
                move.sudo().update({
                    'price_unit': move.sd_precio_unitario,
                })
            # move.sudo().update({
            #     'picking_type_id':move.raw_material_production_id.picking_type_id,
            #     'price_unit': move.sd_precio_unitario,
            #     'availability': move.product_uom_qty,
            #     'location_dest_id': move.raw_material_production_id.production_location_id,
            #     'sd_almacen_destino': None,
            #     'warehouse_id': move.raw_material_production_id.location_src_id.get_warehouse().id,
            #
            # })
    def _action_cancel(self):
        res = super(InheritMrpProduction, self)._action_cancel()
        if self.sd_extras_move_ids:
            raw_moves = self.sd_extras_move_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            raw_moves._action_cancel()
        return res
    def action_assign(self):
        res = super(InheritMrpProduction, self).action_assign()
        for production in self:
            production.sd_extras_move_ids._action_assign()
        return res
    def button_mark_done(self):
        #     print('in function price')
        res = super(InheritMrpProduction, self).button_mark_done()
        self.sd_extras_move_ids.filtered(lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })
        return res
    def post_inventory(self):
        for production in self:
            production.action_cambiar_precio_unitario_product_service()
        res = super(InheritMrpProduction, self).post_inventory()
        for order in self:
            moves_to_do = order.sd_extras_move_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            for move in moves_to_do.filtered(lambda m: m.product_qty == 0.0 and m.quantity_done > 0):
                move.product_uom_qty = move.quantity_done
            moves_to_do = moves_to_do._action_done()
        return res
    def action_view_stock_valuation_layers(self):
        self.ensure_one()
        if self.sd_componentes_extras:
            domain = [('id', 'in', (self.move_raw_ids + self.move_finished_ids + self.scrap_ids.move_id + self.sd_extras_move_ids).stock_valuation_layer_ids.ids)]
        else:
            domain = [('id', 'in', (
                        self.move_raw_ids + self.move_finished_ids + self.scrap_ids.move_id).stock_valuation_layer_ids.ids)]
        action = self.env.ref('stock_account.stock_valuation_layer_action').read()[0]
        context = literal_eval(action['context'])
        context.update(self.env.context)
        context['no_at_date'] = True
        return dict(action, domain=domain, context=context)
class SdInheritMrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"
    def do_produce(self):
        """ Save the current wizard and go back to the MO. """
        res = super(SdInheritMrpProductProduce, self).do_produce()
        if self.production_id.sd_extras_move_ids:
            moves_to_do = self.production_id.sd_extras_move_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            for move in moves_to_do.filtered(lambda m: m.quantity_done == 0.0):
                move.quantity_done = move.product_uom_qty
        return res