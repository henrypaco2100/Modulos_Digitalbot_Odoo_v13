from odoo import api, fields, models, _, tools

class SdInheritPurchaseOrderMejoras(models.Model):
    _inherit = 'purchase.order'
    sd_picking_name = fields.Char(string='Recepciones', compute='_compute_recepciones_name')
    sd_invoice_name = fields.Char(string='Facturas', compute='_compute_facturas_name')
    sd_items_name = fields.Char(string='Productos y Monto', compute='_compute_productos_name')


    @api.depends('order_line')
    def _compute_productos_name(self):

        for record in self:
            record.sd_items_name = ''
            for order in record.order_line:
                signo = ']'
                posicion = order.name.find(signo)
                new_order = order.name[(posicion + 1):]
                record.update({
                    # "sd_items_name": record.sd_items_name + " " + new_order + " | "
                    "sd_items_name": record.sd_items_name + " producto: " + new_order + " : " + str(order.price_subtotal) + " Bs." + " / " + "\n"
                })


    @api.depends('picking_ids')
    def _compute_recepciones_name(self):
        for record in self:
            record.sd_picking_name = ""
            for picking_id in record.picking_ids:
                record.update({
                    "sd_picking_name":record.sd_picking_name + " " + picking_id.name
                })

    @api.depends('invoice_ids')
    def _compute_facturas_name(self):
        for record in self:
            record.sd_invoice_name = ""
            for invoice_id in record.invoice_ids:
                record.update({
                    "sd_invoice_name": record.sd_invoice_name + ", " + invoice_id.name
                })

# class SdInheritPurchaseOrderLIne(models.Model):
#     _inherit = 'purchase.order.line'
#     _rec_name = '' campo a visualizar del modelo