# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError, UserError
import pytz

class InheritPurchase(models.Model):
    _inherit = 'purchase.order'
    date_order_2 = fields.Datetime('Fecha de orden')

    def action_actualizar_fechas(self):
        date_raiz = self.date_order_2
        if date_raiz:
            date_raiz, date_order_factura = self.obtener_fecha_zona_horaria(date_raiz)
            for line in self.order_line:
                line.write({'date_order': date_raiz})
                line.write({'date_planned': date_raiz})

            self.actualizar_fecha_recepcion(date_raiz)
            self.actualizar_fecha_facturas(date_raiz, date_order_factura)

    def actualizar_fecha_facturas(self, date, date_line):
        invoices = self.invoice_ids
        for invoice in invoices:
            invoice.write({
                'date': date_line,
                'invoice_date': date_line,
            })
            for invoice_line in invoice.invoice_line_ids:
                invoice_line.write({'date': date_line})

            for line_id in invoice.line_ids:
                line_id.write({'date': date_line})

    def actualizar_fecha_recepcion(self, date):
        pickings = self.picking_ids
        for line in pickings:
            line.write({
                # 'scheduled_date': date,
                'date_done': date
            })
            # movimientos de existencia
            for existencia_line in line.move_lines:
                existencia_line.write({'date': date,
                                       'date_expected': date})

                for layer in existencia_line.stock_valuation_layer_ids:
                    if not layer.stock_landed_cost_id:
                        parametros = []
                        parametros.append(date)
                        parametros.append(layer.id)
                        self.env.cr.execute(
                            "UPDATE public.stock_valuation_layer SET create_date=%s WHERE id=%s ", (parametros))

            # movimiento de productos
            for productos_line in line.move_line_ids:
                productos_line.write({'date': date})

    def obtener_fecha_hora_actual(self):
        """ Obtener time actual  """

        date_actual = fields.Datetime.now().strftime('%H:%M:%S')
        date_purchase = self.date_order.strftime('%Y-%m-%d')
        date_inherit = date_purchase + ' ' + date_actual
        date_inherit = datetime.strptime(date_inherit, '%Y-%m-%d %H:%M:%S')
        return date_inherit

    def obtener_fecha_zona_horaria(self, date):
        user_tz = self.env.user.tz
        local = pytz.timezone(user_tz)
        date_order_factura = (pytz.utc.localize(date).astimezone(local)).date()
        return date, date_order_factura