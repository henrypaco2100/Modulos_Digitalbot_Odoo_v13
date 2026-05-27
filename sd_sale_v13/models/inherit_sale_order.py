from odoo import api, fields, models, _, tools

class SdInheritSaleOrdenMejoras(models.Model):
    _inherit = 'sale.order'
    sd_invoice_name_sale = fields.Char(string="Facturas", compute='_compute_facturas_name_sale', store=False)
    sd_pickname_name_sale= fields.Char(string="Entregas", compute='_compute_recepciones_name', store=False)
    sd_items__sale_name = fields.Char(string='Productos y Monto', compute='_compute_productos_sale_name')

    @api.depends('order_line')
    def _compute_productos_sale_name(self):
        for record in self:
            record.sd_items__sale_name = ''
            for order in record.order_line:
                signo = ']'
                posicion = order.name.find(signo)
                new_order = order.name[(posicion + 1):]
                record.update({
                    "sd_items__sale_name": record.sd_items__sale_name + " producto: " + new_order + " : " + str(
                        order.price_subtotal) + " Bs." + " / " + "\n"
                })

    @api.depends('invoice_ids')
    def _compute_facturas_name_sale(self):
        for record in self:
            record.sd_invoice_name_sale = ""
            for invoice_id in record.invoice_ids:
                record.update({
                    "sd_invoice_name_sale":record.sd_invoice_name_sale + " " + invoice_id.name
                })

    @api.depends('picking_ids')
    def _compute_recepciones_name(self):
        for record in self:
            record.sd_pickname_name_sale = ""
            for picking_id in record.picking_ids:
                record.update({
                    "sd_pickname_name_sale": record.sd_pickname_name_sale + " " + picking_id.name
                })