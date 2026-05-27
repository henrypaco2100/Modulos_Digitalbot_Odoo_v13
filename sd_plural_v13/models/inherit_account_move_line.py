from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError, UserError, ValidationError
class InheritAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    produccion = fields.Many2one('mrp.production',domain=[('state', '=', 'draft')],string='Producción',copy=False)
    sd_is_produccion = fields.Boolean('Referencia de Producción',store=True, compute="_compute_line_mrp_creation",copy=False)
    @api.depends('produccion','move_id.invoice_line_ids.produccion',)
    def _compute_line_mrp_creation(self):
        for record in self:
            if record.produccion.state == 'draft' and record.move_id.type=='in_invoice' and not record.sd_is_produccion and record.product_id.uom_id:
                if record.product_id in record.produccion.move_raw_ids.mapped('product_id'):
                    for move in record.produccion.move_raw_ids.filtered(lambda x: x.product_id == record.product_id):
                        move.sd_precio_unitario += record.price_subtotal
                else:
                    val = {
                        'name': record.produccion.name,
                        'product_uom_qty':record.quantity,
                        'availability':record.quantity,
                        'raw_material_production_id':record.produccion.id,
                        'reference':record.produccion.name,
                        'sd_precio_unitario':record.price_subtotal,
                        'price_unit': record.price_subtotal,
                        'product_id':record.product_id.id,
                        'product_uom':record.product_uom_id.id or record.product_id.uom_id.id,
                        'location_id':record.produccion.location_src_id.id,
                        'location_dest_id':record.produccion.production_location_id.id,
                        'picking_type_id':record.produccion.picking_type_id.id,
                        'warehouse_id': record.produccion.location_src_id.get_warehouse().id,
                        'display_name': 'Stock>My Company: Production',
                    }
                    raw_move_id = record.env['stock.move'].sudo().create(val)
                record.sd_is_produccion = True
    def _get_computed_name(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id

        values = []
        if product.name:
            values.append(product.name)
        if self.journal_id.type == 'sale':
            if product.description_sale:
                values.append(product.description_sale)
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        return '\n'.join(values)

