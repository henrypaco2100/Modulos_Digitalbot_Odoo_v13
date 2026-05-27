from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round as round, float_compare

class SDInheritAutomatedSaleSiat(models.Model):
    _inherit = 'sale.order'

    def create_and_confirm_invoice(self, date_order_factura_pago):
        """Crear y confirmar factura,
         tambien realizara el pago si es Necesario"""

        create_invoice = self._create_invoices()
        invoice_obj = self.env['account.move'].search([('invoice_origin', '=', self.name), ('state', '!=', 'cancel')])

        if self.work_process_order_id.sales_journal:
            invoice_obj.write({
                'journal_id': self.work_process_order_id.sales_journal.id,
                'invoice_date': date_order_factura_pago,
                'invoice_date_due': date_order_factura_pago,
                'date': date_order_factura_pago,
                'sd_metodo_pago': self.sd_metodo_pago.id
            })
        # Numero de recibo
        if self.sd_is_nro_recibo:
            existe_recibo = True
            if self.work_process_order_id.validate_invoice:
                existe_recibo = True if self.sd_numero_recibo else False
            invoice_obj.write({
                'sd_numero_recibo': self.sd_numero_recibo,
                'sd_is_numero_recibo': existe_recibo,
            })
        # NUemro de factura
        if self.sd_is_nro_factura:
            existe_factura = True
            if self.work_process_order_id.validate_invoice:
                existe_factura = True if self.sd_numero_factura else False
            invoice_obj.write({
                'sd_numero_factura': self.sd_numero_factura,
                'sd_is_numero_factura': existe_factura,
            })
        # referencia Entrega
        if self.sd_is_ref:
            existe_factura = True
            if self.work_process_order_id.validate_invoice:
                existe_factura = True if self.sd_ref_entrega else False
            invoice_obj.write({
                'sd_ref_entrega_sale': self.sd_ref_entrega,
                'sd_is_ref_sale': existe_factura,
            })

        if self.work_process_order_id.register_payment == True and self.work_process_order_id.validate_invoice == True:
            self.create_payment(invoice_obj, date_order_factura_pago)
            # escribir fecha apuntes contables glosa apuntes contable
            objeto_move_line = self.env['account.move.line'].search([('move_id', '=', invoice_obj.id)])
            if objeto_move_line:
                for account_move_line in objeto_move_line.filtered(lambda l: l.exclude_from_invoice_tab == True):
                    account_move_line.name = 'Factura del Cliente ' + invoice_obj.name + ', Venta: ' + self.name


        elif self.work_process_order_id.validate_invoice == True:  # or self.work_process_order_id.force_invoice==True
            validate = invoice_obj.action_post()

            # escribir fecha apuntes contables glosa apuntes contable
            objeto_move_line = self.env['account.move.line'].search([('move_id', '=', invoice_obj.id)])
            if objeto_move_line:
                for account_move_line in objeto_move_line.filtered(lambda l: l.exclude_from_invoice_tab == True):
                    account_move_line.name = 'Factura del Cliente ' + invoice_obj.name + ', Venta: ' + self.name
