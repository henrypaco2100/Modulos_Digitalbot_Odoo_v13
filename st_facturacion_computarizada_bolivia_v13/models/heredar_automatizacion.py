from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
from datetime import date,datetime
from odoo.exceptions import UserError, ValidationError
import datetime

class InheritAutomatedSale(models.Model):
    _inherit = 'sale.order'
    # Herencia de la Automatizacion de Ventas Para Modificar el Nº Factura computarizado
    @api.model
    def action_automated(self):
        if self.work_process_order_id:

            # creamos una variable de fecha global para utilizarla en crear entrega, factura y mas
            date_order = self.date_order
            date_order_factura_pago = (date_order - datetime.timedelta(hours=4)).date()

            # 		<<<<<<<< 			Modificar orden automated
            date_order_2 = self.date_order

            if self.st_orden_cancelada:

                # sobre-escribir fecha
                date_order_factura_pago_2 = (date_order - datetime.timedelta(hours=4)).date()
                nombre_orden_anterior = self.name

                # factura
                objeto_factura_anterior = self.env['account.move'].search([('invoice_origin', '=', self.name)])
                objeto_factura_anterior = self.modificar_la_primera_factura(objeto_factura_anterior)

                id_factura = objeto_factura_anterior.id
                numero_secuencia_siguiente = 0
                numero_actual_factura_computarizada = 0

                # picking
                objeto_picking_anterior = self.env['stock.picking'].search([('origin', '=', self.name)])
                id_picking_anterior = objeto_picking_anterior.id
                numero_secuencia_siguiente_picking = 0

                # orden
                numero_secuencia_siguiente_orden = 0

                # pago
                numero_secuencia_siguiente_pago_diario = 0
                numero_secuencia_siguiente_pago_in = 0

                if self.nombre_secuencia_orden(self.name) == self.nombre_secuencia_orden(
                        self.work_process_order_id.st_secuencia.prefix):
                    cambio_automated = False

                    # factura anterior

                    if objeto_factura_anterior:
                        fecha_creacion = objeto_factura_anterior.create_date
                        date_order_factura_pago = objeto_factura_anterior.invoice_date
                        secuencia_factura_anterior = objeto_factura_anterior.journal_id.sequence_id
                        fecha_anterior_factura = objeto_factura_anterior.invoice_date

                        if objeto_factura_anterior.name != '/':

                            numero_anterior_secuencia = self.obtener_numero_de_secuencia(objeto_factura_anterior.name)

                            # secuencia de la factura

                            if secuencia_factura_anterior.use_date_range:

                                for secuencia_rango in secuencia_factura_anterior.date_range_ids:
                                    if secuencia_rango.date_from <= fecha_anterior_factura and fecha_anterior_factura <= secuencia_rango.date_to:
                                        numero_secuencia_siguiente = secuencia_rango.number_next_actual
                                        secuencia_rango.write({
                                            'number_next_actual': numero_anterior_secuencia, })
                                        break
                            else:
                                numero_secuencia_siguiente = secuencia_factura_anterior.number_next_actual
                                secuencia_factura_anterior.write({
                                    'number_next_actual': numero_anterior_secuencia,
                                })
                        # Modificacion al Metodo Heredado
                        # Numero Factura Computarizado

                        if objeto_factura_anterior.fcb_numero_factura_computarizada:
                            print('ful prueba')
                            if objeto_factura_anterior.journal_id:
                                numero_actual_factura_computarizada = objeto_factura_anterior.journal_id.fcb_siguiente_Numero
                                objeto_factura_anterior.journal_id.write({
                                    'fcb_siguiente_Numero':int(objeto_factura_anterior.fcb_numero_factura_computarizada)
                                })

                        # Pago Factura

                        objeto_pago_anterior = self.env['account.payment'].search(
                            [('communication', '=', objeto_factura_anterior.name)])
                        if objeto_pago_anterior:
                            id_pago = objeto_pago_anterior.id
                            numero_secuencia_anterior_pago_diario = self.obtener_numero_de_secuencia(
                                objeto_pago_anterior.move_name)
                            numero_secuencia_anterior_pago_in = self.obtener_numero_de_secuencia(objeto_pago_anterior.name)
                            fecha_anterior_pago = objeto_pago_anterior.payment_date

                            # secuencia pago Diario

                            secuencia_objeto_pago_diario = objeto_pago_anterior.journal_id.sequence_id
                            if secuencia_objeto_pago_diario.use_date_range:

                                for secuencia_rango in secuencia_objeto_pago_diario.date_range_ids:
                                    if secuencia_rango.date_from <= fecha_anterior_pago and fecha_anterior_pago <= secuencia_rango.date_to:
                                        numero_secuencia_siguiente_pago_diario = secuencia_rango.number_next_actual
                                        secuencia_rango.write({
                                            'number_next_actual': numero_secuencia_anterior_pago_diario, })
                                        break
                            else:
                                numero_secuencia_siguiente_pago_diario = secuencia_objeto_pago_diario.number_next_actual
                                secuencia_objeto_pago_diario.write({
                                    'number_next_actual': numero_secuencia_anterior_pago_diario,
                                })

                            # secuencia pago venta in

                            secuencia_objeto_in_pago = self.env['ir.sequence'].search(
                                [('code', '=', 'account.payment.customer.invoice')])

                            if secuencia_objeto_in_pago.use_date_range:

                                for secuencia_rango in secuencia_objeto_in_pago.date_range_ids:
                                    if secuencia_rango.date_from <= fecha_anterior_pago and fecha_anterior_pago <= secuencia_rango.date_to:
                                        numero_secuencia_siguiente_pago_in = secuencia_rango.number_next_actual
                                        secuencia_rango.write({
                                            'number_next_actual': numero_secuencia_anterior_pago_in, })
                                        break
                            else:
                                numero_secuencia_siguiente_pago_in = secuencia_objeto_in_pago.number_next_actual
                                secuencia_objeto_in_pago.write({
                                    'number_next_actual': numero_secuencia_anterior_pago_in,
                                })

                            self.env.cr.execute("DELETE from account_payment where id=%d" % (id_pago))

                        self.env.cr.execute("DELETE from account_move where id=%d" % (id_factura))

                    # Picking

                    if objeto_picking_anterior:
                        if objeto_picking_anterior.date_done:
                            date_order = objeto_picking_anterior.date_done
                            self.date_order = objeto_picking_anterior.date_done
                        else:
                            date_order = objeto_picking_anterior.scheduled_date
                            self.date_order = objeto_picking_anterior.scheduled_date
                        secuencia_picking_anterior = objeto_picking_anterior.picking_type_id.sequence_id

                        numero_anterior_secuencia_picking = self.obtener_numero_de_secuencia(objeto_picking_anterior.name)

                        if secuencia_picking_anterior.use_date_range:

                            for secuencia_rango in secuencia_picking_anterior.date_range_ids:

                                if secuencia_rango.date_from <= date_order.date() and date_order.date() <= secuencia_rango.date_to:
                                    numero_secuencia_siguiente_picking = secuencia_rango.number_next_actual

                                    secuencia_rango.write({
                                        'number_next_actual': numero_anterior_secuencia_picking, })

                                    break

                        else:
                            numero_secuencia_siguiente_picking = secuencia_picking_anterior.number_next_actual
                            secuencia_picking_anterior.write({
                                'number_next_actual': numero_anterior_secuencia_picking,
                            })
                        self.env.cr.execute("DELETE from stock_picking where id=%d" % (id_picking_anterior))

                    # Orden de venta

                    objeto_secuencia_anterior = self.anterior_secuencia_objeto(nombre_orden_anterior)

                    numero_anterior_secuencia_orden = self.obtener_numero_de_secuencia(nombre_orden_anterior)

                    if objeto_secuencia_anterior.use_date_range:

                        for secuencia_rango in objeto_secuencia_anterior.date_range_ids:
                            if secuencia_rango.date_from <= date_order.date() and date_order.date() <= secuencia_rango.date_to:
                                numero_secuencia_siguiente_orden = secuencia_rango.number_next_actual
                                secuencia_rango.write({
                                    'number_next_actual': numero_anterior_secuencia_orden, })
                                break

                    else:
                        numero_secuencia_siguiente_orden = objeto_secuencia_anterior.number_next_actual

                        objeto_secuencia_anterior.write({
                            'number_next_actual': numero_anterior_secuencia_orden,
                        })
                else:
                    cambio_automated = True

                    # factura
                    if objeto_factura_anterior:
                        objeto_pago_anterior = self.env['account.payment'].search(
                            [('communication', '=', objeto_factura_anterior.ref)])
                        if not objeto_pago_anterior:
                            objeto_pago_anterior = self.env['account.payment'].search(
                                [('communication', '=', objeto_factura_anterior.name)])
                        if objeto_pago_anterior:
                            self.env.cr.execute("DELETE from account_payment where id=%d" % (objeto_pago_anterior.id))
                        self.env.cr.execute("DELETE from account_move where id=%d" % (id_factura))

                    # picking
                    if objeto_picking_anterior:
                        objeto_stock_move = self.env['stock.move'].search(
                            [('picking_id', '=', objeto_picking_anterior.id)])
                        if objeto_stock_move:
                            for stock_move in objeto_stock_move:
                                objeto_account_stock = self.env['account.move'].search(
                                    [('stock_move_id', '=', stock_move.id)])
                                if objeto_account_stock:
                                    for account_move in objeto_account_stock:
                                        self.env.cr.execute("DELETE from account_move where id=%d" % (account_move.id))
                        self.env.cr.execute("DELETE from stock_picking where id=%d" % (id_picking_anterior))

            # Automate Normal

            # Order Configuration
            print("automate factura")
            self.picking_policy = self.work_process_order_id.shipping_policy
            for line in self.order_line:
                parametros = []
                parametros.append(self.work_process_order_id.invoicing_policy)
                parametros.append(line.product_id.id)
                self.env.cr.execute("UPDATE public.product_template SET invoice_policy=%s WHERE id=%s ", (parametros))

            if self.work_process_order_id.validation_order == True:
                picking_confirm = self.action_confirm()
                for order in self:
                    picking_obj = self.env['stock.picking'].search([('origin', '=', order.name)])
                    if self.work_process_order_id.validation_picking == True or self.work_process_order_id.force_transfer == True:

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
                        # escribir fecha en movimiento existencias, asientos contables, productos y valoracion de inventario
                        objeto_stock_move = self.env['stock.move'].search([('picking_id', '=', picking_obj.id)])
                        if objeto_stock_move:
                            for stock_move in objeto_stock_move:
                                stock_move.write({'date': date_order_2})
                                objeto_account_move = self.env['account.move'].search(
                                    [('stock_move_id', '=', stock_move.id)])
                                if objeto_account_move:
                                    for account_move in objeto_account_move:
                                        account_move.write({'date': date_order_factura_pago})
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

                        objeto_stock_move_line = self.env['stock.move.line'].search([('picking_id', '=', picking_obj.id)])
                        if objeto_stock_move_line:
                            for stock_move_line in objeto_stock_move_line:
                                stock_move_line.write({'date': date_order_2})
            if self.work_process_order_id.create_incoice == True:

                create_invoice = self._create_invoices()
                invoice_obj = self.env['account.move'].search(
                    [('invoice_origin', '=', self.name), ('state', '!=', 'cancel')])

                if self.work_process_order_id.sales_journal:
                    invoice_obj.write({
                        'journal_id': self.work_process_order_id.sales_journal.id,
                        'invoice_date': date_order_factura_pago,
                        'invoice_date_due': date_order_factura_pago,
                        'date': date_order_factura_pago,
                    })
                    if self.st_orden_cancelada:
                        self.escribir_fecha_creacion_(invoice_obj, fecha_creacion)
                        self.st_orden_cancelada = False

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

            #          ----------------------------------- Modificar Orden --------------------------------------------
            # volver la secuencia a su numero normal

            if self.st_orden_cancelada:
                self.st_orden_cancelada = False
                # retroceso de secuencias
                if not cambio_automated:
                    # Factura
                    if numero_secuencia_siguiente != 0:

                        if secuencia_factura_anterior.use_date_range:
                            for secuencia_rango in secuencia_factura_anterior.date_range_ids:
                                if secuencia_rango.date_from <= fecha_anterior_factura and fecha_anterior_factura <= secuencia_rango.date_to:
                                    secuencia_rango.write({
                                        'number_next_actual': numero_secuencia_siguiente, })
                                    break
                        else:

                            secuencia_factura_anterior.write({
                                'number_next_actual': numero_secuencia_siguiente,
                            })

                        # sobreescribir fecha factura

                        invoice_obj.write({
                            'invoice_date': date_order_factura_pago_2,
                            'invoice_date_due': date_order_factura_pago_2,
                            'date': date_order_factura_pago_2

                        })
                        objeto_move_line = self.env['account.move.line'].search([('move_id', '=', invoice_obj.id)])
                        if objeto_move_line:
                            for account_move_line in objeto_move_line:
                                account_move_line.write({
                                    'date': date_order_factura_pago_2,
                                    'date_maturity': date_order_factura_pago_2,
                                })

                        # Modificacion al Metodo Heredado
                        # Numero Factura Computarizado

                        if numero_actual_factura_computarizada !=0:
                            invoice_obj.journal_id({
                                'fcb_siguiente_Numero':numero_actual_factura_computarizada,
                            })

                    # Picking

                    if numero_secuencia_siguiente_picking != 0:

                        if secuencia_picking_anterior.use_date_range:

                            for secuencia_rango in secuencia_picking_anterior.date_range_ids:

                                if secuencia_rango.date_from <= date_order.date() and date_order.date() <= secuencia_rango.date_to:
                                    secuencia_rango.write({
                                        'number_next_actual': numero_secuencia_siguiente_picking, })
                                    break
                        else:

                            secuencia_picking_anterior.write({
                                'number_next_actual': numero_secuencia_siguiente_picking,
                            })
                        # sobre-escribir fecha picking
                        if picking_obj.state == 'done':
                            picking_obj.write({'state': 'draft'})
                            picking_obj.write({
                                'date_done': date_order_2,
                                'scheduled_date': date_order_2,
                            })
                            picking_obj.write({'state': 'done'})

                        objeto_stock_move = self.env['stock.move'].search([('picking_id', '=', picking_obj.id)])
                        if objeto_stock_move:
                            for stock_move in objeto_stock_move:
                                stock_move.write({
                                    'date': date_order_2
                                })
                                objeto_account_move = self.env['account.move'].search(
                                    [('stock_move_id', '=', stock_move.id)])
                                if objeto_account_move:
                                    for account_move in objeto_account_move:
                                        account_move.write({
                                            'date': date_order_factura_pago_2
                                        })
                        objeto_stock_move_line = self.env['stock.move.line'].search([('picking_id', '=', picking_obj.id)])
                        if objeto_stock_move_line:
                            for stock_move_line in objeto_stock_move_line:
                                stock_move_line.write({
                                    'date': date_order_2
                                })

                    # Orden

                    if numero_secuencia_siguiente_orden != 0:

                        if objeto_secuencia_anterior.use_date_range:

                            for secuencia_rango in objeto_secuencia_anterior.date_range_ids:
                                if secuencia_rango.date_from <= date_order.date() and date_order.date() <= secuencia_rango.date_to:
                                    secuencia_rango.write({
                                        'number_next_actual': numero_secuencia_siguiente_orden, })
                                    break

                        else:

                            objeto_secuencia_anterior.write({
                                'number_next_actual': numero_secuencia_siguiente_orden,
                            })
                        # sobre-escribir fecha orden
                        self.write({
                            'date_order': date_order_2
                        })

                    # Pago

                    if numero_secuencia_siguiente_pago_in != 0 and numero_secuencia_siguiente_pago_diario != 0:

                        # realizar pago
                        if not self.work_process_order_id.register_payment == True:

                            if not self.work_process_order_id.create_incoice == True:
                                # crear factura

                                create_invoice = self._create_invoices()
                                invoice_obj = self.env['account.move'].search(
                                    [('invoice_origin', '=', self.name), ('state', '!=', 'cancel')])

                                if self.work_process_order_id.sales_journal:
                                    invoice_obj.write({
                                        'journal_id': self.work_process_order_id.sales_journal.id,
                                        'invoice_date': date_order_factura_pago,
                                        'invoice_date_due': date_order_factura_pago,
                                        'date': date_order_factura_pago
                                    })

                                payment = self.env['account.payment']

                                payment_method = self.env['account.payment.method'].search([], limit=1)

                            # publicar factura

                            if not self.work_process_order_id.validate_invoice == True or not self.work_process_order_id.force_invoice == True:

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

                                        'name': self.env['ir.sequence'].with_context(
                                            ir_sequence_date=res.payment_date).next_by_code(sequence_code),
                                    })

                                    inv.reconciled = True
                                    inv.action_invoice_paid()

                                    pay_confirm = res

                                    pay_confirm.post()

                        # secuencia pago Diario

                        if secuencia_objeto_pago_diario.use_date_range:
                            for secuencia_rango in secuencia_objeto_pago_diario.date_range_ids:
                                if secuencia_rango.date_from <= fecha_anterior_pago and fecha_anterior_pago <= secuencia_rango.date_to:
                                    secuencia_rango.write({
                                        'number_next_actual': numero_secuencia_siguiente_pago_diario, })
                                    break
                        else:

                            secuencia_objeto_pago_diario.write({
                                'number_next_actual': numero_secuencia_siguiente_pago_diario,
                            })

                        # secuencia pago in

                        if secuencia_objeto_in_pago.use_date_range:
                            for secuencia_rango in secuencia_objeto_in_pago.date_range_ids:
                                if secuencia_rango.date_from <= fecha_anterior_pago and fecha_anterior_pago <= secuencia_rango.date_to:
                                    secuencia_rango.write({
                                        'number_next_actual': numero_secuencia_siguiente_pago_in, })
                                    break
                        else:

                            secuencia_objeto_in_pago.write({
                                'number_next_actual': numero_secuencia_siguiente_pago_in,
                            })

                        # sobre-escribir fecha pago
                        res.write({
                            'payment_date': date_order_factura_pago_2
                        })
                        # sobre-escrbir efectivo
                        objeto_efectivo = self.env['account.move'].search([('ref', '=', invoice_obj.name)])
                        if objeto_efectivo:
                            for efectivo in objeto_efectivo:
                                efectivo.write({
                                    'date': date_order_factura_pago_2,
                                })
                            objeto_move_line = self.env['account.move.line'].search([('move_id', '=', objeto_efectivo.id)])
                            if objeto_move_line:
                                for account_move_line in objeto_move_line:
                                    account_move_line.write({
                                        'date': date_order_factura_pago_2,
                                        'date_maturity': date_order_factura_pago_2,
                                    })








        else:
            raise Warning(('El proceso de flujo de trabajo no se ha indicado, indique el proceso de flujo de trabajo.'))

        return super().action_automated()
