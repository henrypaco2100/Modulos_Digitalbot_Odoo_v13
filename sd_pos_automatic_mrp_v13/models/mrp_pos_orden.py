from odoo import api, fields, models, _, tools
from odoo.exceptions import AccessError, UserError, ValidationError

class posOrderMrp(models.Model):
    _inherit = "pos.session"


    def action_pos_session_closing_control(self):
        id_ruta_mrp = self.env['ir.model.data'].xmlid_to_res_id("mrp.route_warehouse0_manufacture")
        vals = super(posOrderMrp, self).action_pos_session_closing_control()
        qty_products = []
        # recorre las ordenes o pedidos
        orders = self.order_ids.filtered(lambda x: x.state != 'cancel')
        for order in orders:
            for line in order.lines:
                if id_ruta_mrp in [route.id for route in line.product_id.route_ids]:
                    if not qty_products or line.product_id not in [pr[0] for pr in qty_products]:
                        #este if añade nuevos productos sino no estan agregados
                        self.add_product(line, qty_products)
                    else:
                        for ele in qty_products:
                            #este for añade cantidades a productos ya agregados
                            if ele[0] == line.product_id:
                                ele[1] += line.qty
        self.create_order_production(qty_products)
        return vals

    def add_product(self, line, qty_products):
        product = [line.product_id, line.qty]
        qty_products.append(product)
        return True
    def create_order_production(self, qty_products):

        for product in qty_products:
            if product[0]._name == 'product.template':
                boom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product[0].id)])
            elif product[0]._name == 'product.product':
                boom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product[0].product_tmpl_id.id)])

            if not boom:
                raise UserError(_(' El producto %s no tiene una lista de materiales.'
                                  'No es posible continuar comuniquese con su soporte henry') % (
                product[0].name))
            vals_mrp = {
                'product_id': product[0].id,
                'product_qty': product[1],
                'product_uom_id': product[0].uom_po_id.id,
                'bom_id': boom.id
            }
            mrp = self.env['mrp.production'].sudo().create(vals_mrp)
            mrp._onchange_move_raw()