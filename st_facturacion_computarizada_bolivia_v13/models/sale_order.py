from odoo import api, fields, models, _


class ihneritSaleOrder(models.Model):
    _inherit = 'sale.order'

    Nit_cliente = fields.Char(readonly=True, string="NIT")
    @api.onchange('date_order','work_process_order_id')
    def controlar_fecha_limite(self):
        if self.work_process_order_id.sales_journal.fcb_fecha_limite_emision and self.work_process_order_id and self.date_order:
            fecha_order = self.date_order.date()
            fecha_limite = self.work_process_order_id.sales_journal.fcb_fecha_limite_emision
            if fecha_order > fecha_limite:
                self.date_order = ""
                return {
                    'warning': {
                        'message': _(
                            f"Dosificacion Caducado, la fecha limite de la factura es: {fecha_limite}. ")
                    }
                }
