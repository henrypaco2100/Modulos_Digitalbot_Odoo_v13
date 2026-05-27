from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
from datetime import date, datetime
import datetime

class InheritPurchaseImport(models.Model):
    _inherit = 'purchase.order'
    def automated_purchase_import(self):
        date_order = self.date_order
        date_order_factura_pago = (date_order - datetime.timedelta(hours=4)).date()

        # sobre-escribir fecha
        date_order_2 = self.date_order  # .strftime('%Y-%m-%d %H:%M:%S')
        date_order_factura_pago_2 = (date_order - datetime.timedelta(hours=4)).date()


        if self.work_process_order_id:
            # Automated Normal

            for line in self.order_line:
                line.product_id.purchase_method = self.work_process_order_id.control_policy

            if self.work_process_order_id.validation_order == True:
                picking_confirm = self.button_confirm()

            if self.work_process_order_id.create_incoice == True:
                account_inv_obj = self.env['account.move']
                vals = {
                    'type': 'in_invoice',
                    'invoice_origin': self.name,
                    'purchase_id': self.id,
                    'partner_id': self.partner_id.id,
                    # ingresamo el diario , la fecha factura Y LA FECHA CONTABLE
                    'journal_id': self.work_process_order_id.purchase_journal.id,
                    'invoice_date': date_order_factura_pago,
                    'date': date_order_factura_pago,
                    'ref': self.partner_ref if self.partner_ref else ''
                }
                res = account_inv_obj.create(vals)
                po_lines = self.order_line
                new_lines = self.env['account.move.line']
                new_lines = []
                for line in po_lines.filtered(lambda l: not l.display_type):
                    new_lines.append((0, 0, line._prepare_account_move_line(res)))
                res.write({
                    'invoice_line_ids': new_lines,
                    'purchase_id': False
                })
                for purchase_line in account_inv_obj.invoice_line_ids:
                    if purchase_line.quantity <= 0:
                        purchase_line.unlink()
                payment = self.env['account.payment']
                payment_method = self.env['account.payment.method'].search([], limit=1)
                if res:
                    if self.work_process_order_id.register_payment == True and self.work_process_order_id.validate_invoice == True:

                        if self.work_process_order_id.purchase_journal:
                            res.journal_id = self.work_process_order_id.purchase_journal
                        validate = res.action_post()
                        payment_order = payment.create({

                            'partner_id': res.partner_id.id,
                            'amount': res.amount_total,
                            'payment_type': 'outbound',
                            'partner_type': 'supplier',
                            'payment_method_id': payment_method.id,
                            'journal_id': self.work_process_order_id.payment_journal.id,
                            'payment_date': date_order_factura_pago,
                            'communication': res.ref if res.ref else res.name,
                            'invoice_ids': [(6, 0, [res.id])]
                        })

                        sequence_code = 'account.payment.vendor.bill'
                        payment_order.write({

                            'name': self.env['ir.sequence'].with_context(
                                ir_sequence_date=payment_order.payment_date).next_by_code(sequence_code),

                        })

                        res.reconciled = True
                        res.action_invoice_paid()
                        pay_confirm = payment = self.env['account.payment'].search([("communication", "=", res.name)])
                        pay_confirm.post()



                    elif self.work_process_order_id.validate_invoice == True or self.work_process_order_id.force_invoice == True:
                        res.action_post()
                        # escribir fecha apuntes contables
                        objeto_move_line = self.env['account.move.line'].search([('move_id', '=', res.id)])
                        if objeto_move_line:
                            for account_move_line in objeto_move_line:
                                account_move_line.write({
                                    'date_maturity': date_order_factura_pago,
                                })

                    else:
                        pass

                for order in self:
                    if self.work_process_order_id.validation_picking == True or self.work_process_order_id.force_transfer == True:
                        picking_obj = self.env['stock.picking'].search([('origin', '=', order.name)])
                        if not picking_obj:
                            order._create_picking()
                            picking_obj = self.env['stock.picking'].search([('origin', '=', order.name)])
                            # escribir la fecha de compra en fecha prevista de orden de entrega
                        picking_obj.write({
                            'scheduled_date': date_order,
                            'date_done': date_order,
                        })
                        for pick in picking_obj:
                            for qty in pick.move_lines:
                                qty.write({
                                    'quantity_done': qty.product_uom_qty,
                                })
                            pick.button_validate()
                            # pick.action_done()

                            for line in order.order_line:
                                line.write({
                                    'qty_received': line.product_uom_qty,
                                })
                        # escribir fecha Movimiento de existencias
                        objeto_stock_move = self.env['stock.move'].search([('picking_id', '=', picking_obj.id)])
                        if objeto_stock_move:
                            for stock_move in objeto_stock_move:
                                stock_move.write({
                                    'date': date_order,
                                })
                                # escribir nombre y fecha Asientos contables de movimiento de existencias
                                objeto_account_move = self.env['account.move'].search(
                                    [('stock_move_id', '=', stock_move.id)])
                                if objeto_account_move:
                                    for account_move in objeto_account_move:
                                        account_move.write({
                                            'date': date_order_factura_pago,
                                            # 'name':self.env['ir.sequence'].with_context(ir_sequence_date=date_order_factura_pago).next_by_code(account_move.journal_id.sequence_id.code)
                                        })

                                # escribir fecha de Valoracion de Inventario
                                objeto_stock_valuation_layer = self.env['stock.valuation.layer'].search(
                                    [('stock_move_id', '=', stock_move.id)])
                                if objeto_stock_valuation_layer:
                                    for stock_valuation_layer in objeto_stock_valuation_layer:
                                        parametros = []
                                        parametros.append(date_order)
                                        parametros.append(stock_valuation_layer.id)
                                        self.env.cr.execute(
                                            "UPDATE public.stock_valuation_layer SET create_date=%s WHERE id=%s ",
                                            (parametros))
                        # escribir fecha Movimiento de productos
                        objeto_stock_move_line = self.env['stock.move.line'].search([('picking_id', '=', picking_obj.id)])
                        if objeto_stock_move_line:
                            for stock_move_line in objeto_stock_move_line:
                                stock_move_line.write({
                                    'date': date_order,
                                })

                    else:
                        return
        else:
            raise Warning(('El proceso de flujo de trabajo no se ha indicado, indique el proceso de flujo de trabajo.'))