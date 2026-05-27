from odoo import api, fields, models,SUPERUSER_ID,_
from odoo.exceptions import UserError

class InheritStockMoveMejoraPlural(models.Model):
    _inherit = "stock.move"

    sd_pvp_product = fields.Float('Precio Venta', compute='compute_pvp_product', store=False)
    sd_material_extra_production_id = fields.Many2one(
        'mrp.production', 'Componentes Extras en Orden de Producion', check_company=True)
    sd_precio_unitario = fields.Float(string='Precio U.',readonly=False)
    sd_total_precio = fields.Float(string='Total',compute='sd_compute_total_precio', store=True)
    # sd_precio_servicio =fields.Float(string='Precio Servicio')
    sd_analitica_proceso = fields.Many2one(string='Analitica', related='raw_material_production_id.sd_account_analitica_out')
    @api.depends('sd_precio_unitario','product_uom_qty','quantity_done')
    def sd_compute_total_precio(self):
        for record in self:
            if record.raw_material_production_id.state in ('done','cancel','to_close') or record.sd_material_extra_production_id.state in ('done','cancel','to_close'):
                record.sd_total_precio = record.sd_precio_unitario * record.quantity_done
            else:
                record.sd_total_precio = record.sd_precio_unitario * record.product_uom_qty

    @api.depends('product_id')
    def compute_pvp_product(self):
        for stock_move_line in self:
            stock_move_line.update({
                'sd_pvp_product': stock_move_line.product_id.lst_price
            })

    @api.onchange('product_id')
    def _onchange_precio_unitario(self):
        for record in self:
            record.sd_precio_unitario = record.product_id.standard_price

    # adicionar cuentas analiticas en asiento produccion Henry
    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id, description):
        # This method returns a dictionary to provide an easy extension hook to modify the valuation lines (see purchase for an example)
        self.ensure_one()
        debit_line_vals = {
            'name': description,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': description,
            'partner_id': partner_id,
            'debit': debit_value if debit_value > 0 else 0,
            'credit': -debit_value if debit_value < 0 else 0,
            'account_id': debit_account_id,
            'analytic_account_id': self.raw_material_production_id.sd_account_analitica_out.id if self.raw_material_production_id else (
                self.sd_material_extra_production_id.sd_account_analitica_out.id if self.sd_material_extra_production_id else None),
        }

        credit_line_vals = {
            'name': description,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': description,
            'partner_id': partner_id,
            'credit': credit_value if credit_value > 0 else 0,
            'debit': -credit_value if credit_value < 0 else 0,
            'account_id': credit_account_id,
            'analytic_account_id': self.raw_material_production_id.sd_account_analitica_out.id if self.raw_material_production_id else (
                self.sd_material_extra_production_id.sd_account_analitica_out.id if self.sd_material_extra_production_id else None),

        }

        rslt = {'credit_line_vals': credit_line_vals, 'debit_line_vals': debit_line_vals}
        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.product_id.property_account_creditor_price_difference

            if not price_diff_account:
                price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
            if not price_diff_account:
                raise UserError(
                    _('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))

            rslt['price_diff_line_vals'] = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': description,
                'partner_id': partner_id,
                'credit': diff_amount > 0 and diff_amount or 0,
                'debit': diff_amount < 0 and -diff_amount or 0,
                'account_id': price_diff_account.id,
            }
        return rslt
    # PARA LOS COMPONENTES EXTRAS
    @api.model
    def default_get(self, fields_list):
        defaults = super(InheritStockMoveMejoraPlural, self).default_get(fields_list)
        if self.env.context.get('default_sd_material_extra_production_id'):
            production_id = self.env['mrp.production'].browse(self.env.context['default_sd_material_extra_production_id'])
            if production_id.state == 'done':
                defaults['state'] = 'done'
                defaults['product_uom_qty'] = 0.0
                defaults['additional'] = True
            elif production_id.state == 'draft':
                defaults['group_id'] = production_id.procurement_group_id.id
                defaults['reference'] = production_id.name
        return defaults
    def _should_be_assigned(self):
        res = super(InheritStockMoveMejoraPlural, self)._should_be_assigned()
        return bool(res and not (self.sd_material_extra_production_id))

    @api.depends('raw_material_production_id.name','sd_material_extra_production_id.name')
    def _compute_reference(self):
        not_prod_move = self.env['stock.move']
        for move in self:
            if not move.sd_material_extra_production_id:
                not_prod_move |= move
                continue
            move.write({
                'name': move.sd_material_extra_production_id.name,
                'reference': move.sd_material_extra_production_id.name,
            })
        super(InheritStockMoveMejoraPlural, not_prod_move)._compute_reference()

    @api.depends('raw_material_production_id.is_locked', 'picking_id.is_locked','sd_material_extra_production_id.is_locked')
    def _compute_is_locked(self):
        super(InheritStockMoveMejoraPlural, self)._compute_is_locked()
        for move in self:
            if move.sd_material_extra_production_id:
                move.is_locked = move.sd_material_extra_production_id.is_locked

