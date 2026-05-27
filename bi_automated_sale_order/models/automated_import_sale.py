from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError


class InheritSaleImport(models.Model):
    _inherit = 'sale.order'
    # secuencia de la factura

    def automated_import_sale(self):

        if self.work_process_order_id:
            date_order= self.date_order
            date_order_factura_pago = date_order.date()

            # Order Configuration
            self.picking_policy = self.work_process_order_id.shipping_policy
            for line in self.order_line:
                line.product_id.invoice_policy = self.work_process_order_id.invoicing_policy

            if self.work_process_order_id.validation_order == True:
                picking_confirm = self.action_confirm()

                for order in self:
                    if self.work_process_order_id.validation_picking == True or self.work_process_order_id.force_transfer == True:
                        picking_obj = self.env['stock.picking'].search([('origin', '=', order.name)])

                        for pick in picking_obj:
                            for qty in pick.move_lines:
                                qty.write({
                                    'quantity_done': qty.product_uom_qty,
                                })

                            pick.button_validate()
                            pick.action_done()

                            for line in order.order_line:
                                line.write({
                                    'qty_delivered': line.product_uom_qty,
                                })
                        # se sobreescribe o modifica la fecha efectiva en orden entrega

                        picking_obj.write({
                            'date_done': date_order
                        })
                        # escribir fecha en movimiento producto y existencias
                        objeto_stock_move = self.env['stock.move'].search([('picking_id', '=', picking_obj.id)])
                        if objeto_stock_move:
                            for stock_move in objeto_stock_move:
                                stock_move.write({
                                    'date': date_order
                                })
                                objeto_account_move = self.env['account.move'].search(
                                    [('stock_move_id', '=', stock_move.id)])
                                if objeto_account_move:
                                    for account_move in objeto_account_move:
                                        account_move.write({
                                            'date': date_order_factura_pago
                                        })
                        objeto_stock_move_line = self.env['stock.move.line'].search([('picking_id', '=', picking_obj.id)])
                        if objeto_stock_move_line:
                            for stock_move_line in objeto_stock_move_line:
                                stock_move_line.write({
                                    'date': date_order
                                })

            if self.work_process_order_id.create_incoice == True:

                create_invoice = self._create_invoices()
                invoice_obj = self.env['account.move'].search([('invoice_origin', '=', self.name)])

                if self.work_process_order_id.sales_journal:
                    invoice_obj.write({
                        'journal_id': self.work_process_order_id.sales_journal.id,
                        'invoice_date': date_order_factura_pago,
                        'invoice_date_due': date_order_factura_pago,
                        'date': date_order_factura_pago,
                    })

                payment = self.env['account.payment']

                payment_method = self.env['account.payment.method'].search([], limit=1)
                if self.work_process_order_id.register_payment == True and self.work_process_order_id.validate_invoice == True:
                    validate = invoice_obj.action_post()

                    for inv in invoice_obj:
                        res = payment.create({

                            'partner_id': inv.partner_id.id,
                            'amount': inv.amount_total,
                            'payment_type': 'inbound',
                            'partner_type': 'customer',
                            'payment_method_id': payment_method.id,
                            'journal_id': self.work_process_order_id.payment_journal.id,
                            'payment_date': date_order_factura_pago,
                            'communication': inv.name,
                            'invoice_ids': [(6, 0, [inv.id])]
                        })

                        sequence_code = 'account.payment.customer.invoice'
                        res.write({

                            'name': self.env['ir.sequence'].with_context(ir_sequence_date=res.payment_date).next_by_code(
                                sequence_code),
                        })

                        inv.reconciled = True
                        inv.action_invoice_paid()

                        pay_confirm = res

                        pay_confirm.post()



                elif self.work_process_order_id.validate_invoice == True or self.work_process_order_id.force_invoice == True:
                    validate = invoice_obj.action_post()

                    # escribir fecha apuntes contables
                    objeto_move_line = self.env['account.move.line'].search([('move_id', '=', invoice_obj.id)])
                    if objeto_move_line:
                        for account_move_line in objeto_move_line:
                            account_move_line.write({
                                'date_maturity': date_order_factura_pago,
                            })
                # invoice_obj._create_invoices()

                else:
                    pass


        else:
            raise Warning(('El proceso de flujo de trabajo no se ha indicado, indique el proceso de flujo de trabajo.'))
