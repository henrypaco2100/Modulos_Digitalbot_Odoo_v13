from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
import datetime
import pytz

class InheritReturnPickingSodigitalim(models.TransientModel):
    _inherit = 'stock.return.picking'

    account_move_id = fields.Many2one('account.move', string='Factura', domain="[('id', '=', account_move_id)]")
    date_returns = fields.Datetime(string='Fecha Devolucion', required=True)

    #heredar factura
    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        res = super(InheritReturnPickingSodigitalim, self)._onchange_picking_id()
        # heredar date_Returns y account_move
        self.date_returns = self._default_date_picking()
        if self.picking_id.sale_id:
            self.account_move_id = self.modificar_la_primera_factura(self.picking_id.sale_id.invoice_ids.filtered(lambda invoice: invoice.state != 'cancel'))
        elif self.picking_id.purchase_id:
            self.account_move_id = self.modificar_la_primera_factura(self.picking_id.purchase_id.invoice_ids.filtered(lambda invoice: invoice.state != 'cancel'))
        return res
    @api.model
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
        quantity = stock_move.product_qty
        for move in stock_move.move_dest_ids:
            if move.state in ('partially_available', 'assigned'):
                quantity -= sum(move.move_line_ids.mapped('product_qty'))
            elif move.state in ('done'):
                quantity -= move.product_qty
        quantity = float_round(quantity, precision_rounding=stock_move.product_uom.rounding)
        #HENRY DEVOLUCION CON FACTURA
        invoice_id =[]
        if stock_move.picking_id.sale_id or stock_move.picking_id.purchase_id:
            if stock_move.picking_id.sale_id:
                invoice_id = self.modificar_la_primera_factura(stock_move.picking_id.sale_id.invoice_ids)
            elif stock_move.picking_id.purchase_id:
                invoice_id = self.modificar_la_primera_factura(stock_move.picking_id.purchase_id.invoice_ids)
        return {
            'product_id': stock_move.product_id.id,
            'quantity': quantity,
            'move_id': stock_move.id,
            'uom_id': stock_move.product_id.uom_id.id,
            # 'account_move_id': invoice_id,
        }
    def modificar_la_primera_factura(self, facturas):
        if len(facturas) > 1:
            facturas = sorted(facturas, key=lambda factura: factura.create_date)
            for factura in facturas:
                factura_primera_creada = factura
                break
            return factura_primera_creada
        else:
            return facturas

    def create_returns(self):
        for wizard in self:
            new_picking_id, pick_type_id = wizard._create_returns()

            # Sodigitalim -HENRY
            mensaje = self.returns_full_(new_picking_id)
        # Override the context to disable all the potential filters that could have been set previously
        ctx = dict(self.env.context)
        ctx.update({
            'search_default_picking_type_id': pick_type_id,
            'search_default_draft': False,
            'search_default_assigned': False,
            'search_default_confirmed': False,
            'search_default_ready': False,
            'search_default_late': False,
            'search_default_available': False,
        })
        #Realizar mensaje
        if mensaje:
            message_id = self.env['returns.message.wizard'].create({'message':mensaje + '.' or ''})
            return {
                'name': 'Proceso Exitoso!!',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'returns.message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }
        # return {
        #     'name': _('Returned Picking'),
        #     'view_mode': 'form,tree,calendar',
        #     'res_model': 'stock.picking',
        #     'res_id': new_picking_id,
        #     'type': 'ir.actions.act_window',
        #     'context': ctx,
        # }
    #Sodigitalim - HENRY

    def returns_full_(self,new_picking_id):
        # Validar Devolucion stock.picking
        object_picking_new = self.env['stock.picking'].search([('id','=',new_picking_id)])
        object_picking_transfer_inmediate= self.env['stock.immediate.transfer'].create({'pick_ids': [(4, object_picking_new.id)]})
        object_picking_transfer_inmediate.process()
        #Escribir Fecha devolucion en picking validado
        self.write_date_returns(object_picking_new)
        # Devolucion
        mensaje = 'Devolucion realizada '
        if object_picking_new.sale_id:
        # realizar Devolucion Venta
            mensaje2=self.returns_sale_(object_picking_new.sale_id)
            mensaje = mensaje + mensaje2

        # Realizar Devolucion Compra
        if object_picking_new.purchase_id:
            mensaje = mensaje + self.returns_purchase_(object_picking_new.purchase_id)

        return mensaje

    def returns_sale_(self, sale):
        if sale:
            for returns_producto in self.product_return_moves:
                # print('name producto returns',returns_producto.product_id.name)
                line_sale_ = sale.order_line.filtered(lambda line_sale: line_sale.product_id == returns_producto.product_id)
                if line_sale_.product_uom_qty >= returns_producto.quantity:
                    line_sale_.write({
                        'product_uom_qty': abs(line_sale_.product_uom_qty) - abs(returns_producto.quantity)
                    })
                else:
                    raise UserError(_(
                        'La cantidad del producto : %s es mayor a la cantidad realizada en el Pedido de Venta.'
                        ) % (returns_producto.product_id.name))
            # devolucion_factura
            if self.account_move_id:
                mensaje = self.returns_invoice_sale(sale)
                return mensaje
            else:
                return ''
        else:
            return ''

    def returns_purchase_(self,purchase):
        if purchase:
            for returns_producto in self.product_return_moves:
                line_purchase = purchase.order_line.filtered(lambda line_purchase: line_purchase.product_id == returns_producto.product_id)
                if line_purchase.product_qty >= returns_producto.quantity:
                    line_purchase.write({
                        'product_qty': abs(line_purchase.product_qty) - abs(returns_producto.quantity)
                    })
                    # line_purchase._compute_amount()
                else:
                    raise UserError(_(
                        'La cantidad del producto : %s es mayor a la cantidad realizada en el Pedido de Compra.'
                        ) % (returns_producto.product_id.name))
            # devolucion_factura
            if self.account_move_id:
                mensaje =self.returns_invoice_purchase(purchase)
                return mensaje
            else:
                return ''
        else:
            return ''
    def returns_invoice_sale(self,orden):
        if orden.invoice_ids and self.account_move_id:
            user_tz = self.env.user.tz
            local = pytz.timezone(user_tz)
            date_order_factura = (pytz.utc.localize(self.date_returns).astimezone(local)).date()
            object_invoice_id = orden.invoice_ids.filtered(lambda invoice: invoice == self.account_move_id)
            # crear mensaje
            mensaje = ', se ha creado una nueva Factura'
            mensaje = self.sd_existen_payment_invoice(object_invoice_id,mensaje)
            object_invoice_id.sudo().button_draft()
            object_invoice_id.sudo().button_cancel()
            sd_name = object_invoice_id.name
            object_invoice_id.sudo().write({
                'name':'Anulada'+' '+ object_invoice_id.name,
                'display_name': 'Anulada' + ' ' + object_invoice_id.name,
            })
            if object_invoice_id.ref:
                object_invoice_id.sudo().write({
                    'ref':'Anulada '+object_invoice_id.ref
                })

            # existen mas de 2 facturas
            if len(orden.invoice_ids) > 1:
                orden.invoice_ids.sudo().button_draft()
                orden.invoice_ids.sudo().button_cancel()

            orden._create_invoices()
            invoice_new = orden.invoice_ids.filtered(lambda invoice: invoice.state != 'cancel')
            if orden.work_process_order_id.sales_journal:
                invoice_new.write({
                    'journal_id': orden.work_process_order_id.sales_journal.id,
                    'invoice_date': date_order_factura,
                    'invoice_date_due': date_order_factura,
                    'date': date_order_factura,
                    'name':sd_name,
                    'display_name':'Factura borrador ' + sd_name
                })
            invoice_new.post()
            return mensaje
        else:
            return ''

    def returns_invoice_purchase(self,orden):
        if orden.invoice_ids and self.account_move_id:
            user_tz = self.env.user.tz
            local = pytz.timezone(user_tz)
            date_order_factura = (pytz.utc.localize(self.date_returns).astimezone(local)).date()
            object_invoice_id = orden.invoice_ids.filtered(lambda invoice: invoice == self.account_move_id)
            mensaje = ', se ha creado una nueva Factura'
            mensaje = self.sd_existen_payment_invoice(object_invoice_id, mensaje)
            object_invoice_id.sudo().button_draft()
            object_invoice_id.sudo().button_cancel()
            sd_name = object_invoice_id.name
            object_invoice_id.sudo().write({
                'name':'Anulada'+' '+ object_invoice_id.name,
                'display_name': 'Anulada' + ' ' + object_invoice_id.name,
            })
            object_invoice_id.sudo().write({
                'ref': 'Anulada ' + object_invoice_id.ref
            })
            # existen mas de 2 facturas
            if len(orden.invoice_ids) > 1:
                orden.invoice_ids.sudo().button_draft()
                orden.invoice_ids.sudo().button_cancel()

            self.create_invoice_purchase_direct(orden,date_order_factura)
            invoice_new = orden.invoice_ids.filtered(lambda invoice: invoice.state != 'cancel')
            if orden.work_process_order_id.purchase_journal:
                invoice_new.write({
                    'journal_id': orden.work_process_order_id.purchase_journal.id,
                    'invoice_date': date_order_factura,
                    'invoice_date_due': date_order_factura,
                    'date': date_order_factura,
                    'name':sd_name,
                    'display_name':'Factura borrador ' + sd_name
                })
            invoice_new.post()
            return mensaje
        else:
            return ''


    def create_invoice_purchase_direct(self,orden,date_order_factura_pago):
        account_inv_obj = self.env['account.move']
        vals = {
            'type': 'in_invoice',
            'invoice_origin': orden.name,
            'purchase_id': orden.id,
            'partner_id': orden.partner_id.id,
            # ingresamo el diario , la fecha factura Y LA FECHA CONTABLE
            'journal_id': orden.work_process_order_id.purchase_journal.id,
            'invoice_date': date_order_factura_pago,
            'date': date_order_factura_pago,
            'ref': orden.partner_ref if orden.partner_ref else '',
            'currency_id': orden.currency_id.id
        }
        res = account_inv_obj.create(vals)
        po_lines = orden.order_line
        new_lines = orden.env['account.move.line']
        new_lines = []
        for line in po_lines.filtered(lambda l: not l.display_type):
            new_lines.append((0, 0, line._prepare_account_move_line(res)))
        res.write({
            'invoice_line_ids': new_lines,
            'purchase_id': orden.id,
        })
        for purchase_line in account_inv_obj.invoice_line_ids:
            if purchase_line.quantity <= 0:
                purchase_line.unlink()
    def sd_existen_payment_invoice(self,invoice, mensaje):
        pagos = self.env['account.payment'].search([('communication','=', invoice.name)])
        if pagos:
            return mensaje + ', no se olvide de añadir los pagos necesarios'
        else:
            return mensaje
    @api.onchange('date_returns')
    def date_returns_no_menor(self):
        user_tz = self.env.user.tz
        local = pytz.timezone(user_tz)
        date_returns = pytz.utc.localize(self.date_returns).astimezone(local)
        if self.picking_id.date_done:
            date_done_picking = pytz.utc.localize(self.picking_id.date_done).astimezone(local)
            if not date_returns >= date_done_picking:
                self.date_returns = self.picking_id.date_done
                return {
                    'warning': {
                        'message': _(
                            f'La Fecha Devolucion no puede ser menor que la fecha de la transferencia. ')
                    }
                }
        elif self.picking_id.scheduled_date:
            scheduled_date_picking = pytz.utc.localize(self.picking_id.scheduled_date).astimezone(local)
            if not self.date_returns >= scheduled_date_picking:
                self.date_returns = self.picking_id.scheduled_date
                return {
                    'warning': {
                        'message': _(
                            f'La Fecha Devolucion no puede ser menor que la fecha de la transferencia. ')
                    }
                }
    def _default_date_picking(self):
        if self.picking_id.date_done:
            return self.picking_id.date_done
        elif self.picking_id.scheduled_date:
            return self.picking_id.scheduled_date
        else:
            return fields.Datetime.now()
    def write_date_returns(self, objeto_devolucion):
        if self.date_returns:
            objeto_devolucion
            # fecha devolucion picking
            parametros = []
            parametros.append(self.date_returns)
            parametros.append(self.date_returns)
            parametros.append(objeto_devolucion.id)
            self.env.cr.execute("UPDATE public.stock_picking SET date_done=%s, scheduled_date =%s WHERE id=%s ", (parametros))

            user_tz = self.env.user.tz
            local = pytz.timezone(user_tz)
            date_invoice = (pytz.utc.localize(self.date_returns).astimezone(local)).date()
            #Produccion
            for stock_move_line in objeto_devolucion.move_line_ids:
                # movimiento de producto
                stock_move_line.sudo().write({
                    'date': self.date_returns
                })
                # movimiento de existencia
                stock_move_line.move_id.sudo().write({
                    'date':self.date_returns
                })
                # valoracion de inventario escribir fecha
                for valoracion in stock_move_line.move_id.stock_valuation_layer_ids:
                    parametros = []
                    parametros.append(self.date_returns)
                    parametros.append(valoracion.id)
                    self.env.cr.execute("UPDATE public.stock_valuation_layer SET create_date=%s WHERE id=%s ", (parametros))
                # asientos de los movimientos escribir fecha
                for account_move in stock_move_line.move_id.account_move_ids:
                    account_move.sudo().write({
                        'date': date_invoice
                    })
            return True
        else:
            return False