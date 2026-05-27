import datetime
from collections import defaultdict
from itertools import groupby
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import date_utils, float_compare, float_round, float_is_zero


class InheritMrpProductionDate(models.Model):
    """ Inherit Manufacturing Orders
        para Modificar fecha
    """
    _inherit = 'mrp.production'

    date_finished = fields.Datetime('Fecha final', copy=False, index=True, readonly=False, default=fields.Datetime.now)

    def post_inventory(self):
        res = super(InheritMrpProductionDate, self).post_inventory()
        #Henry Escribir Fecha
        if 'done' == self.state:
            write_date = self.write_date_finished()
    def write_date_finished(self):
        if self.date_finished:
            user_tz = self.env.user.tz
            local = pytz.timezone(user_tz)
            date_invoice = pytz.utc.localize(self.date_finished).astimezone(local)
            #Produccion
            for stock_move_line in self.finished_move_line_ids:
                # movimiento de producto
                stock_move_line.sudo().write({
                    'date': self.date_finished
                })
                # movimiento de existencia
                stock_move_line.move_id.sudo().write({
                    'date':self.date_finished
                })
                # valoracion de inventario escribir fecha
                for valoracion in stock_move_line.move_id.stock_valuation_layer_ids:
                    parametros = []
                    parametros.append(self.date_finished)
                    parametros.append(valoracion.id)
                    self.env.cr.execute("UPDATE public.stock_valuation_layer SET create_date=%s WHERE id=%s ", (parametros))
                # asientos de los movimientos escribir fecha
                for account_move in stock_move_line.move_id.account_move_ids:
                    account_move.sudo().write({
                        'date': date_invoice
                    })
            # Componentes
            for move in self.move_raw_ids:
                move.sudo().write({
                    'date':self.date_finished
                })
                # escribir fecha movimiento de producto
                object_move_line = self.env['stock.move.line'].search([('move_id','=',move.id)])
                for move_line in object_move_line:
                    move_line.sudo().write({
                        'date':self.date_finished
                    })
                # escribir fecha asiento contable
                for account_move in move.account_move_ids:
                    account_move.sudo().write({
                        'date': date_invoice
                    })
                # escribir fecha valoracion
                for stock_valuation in move.stock_valuation_layer_ids:
                    parametros = []
                    parametros.append(self.date_finished)
                    parametros.append(stock_valuation.id)
                    self.env.cr.execute("UPDATE public.stock_valuation_layer SET create_date=%s WHERE id=%s ", (parametros))
            return True
        else:
            return False
    def button_mark_done(self):
        self.ensure_one()
        self._check_company()
        for wo in self.workorder_ids:
            if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                raise UserError(_('Work order %s is still running') % wo.name)
        self._check_lots()

        self.post_inventory()
        # Moves without quantity done are not posted => set them as done instead of canceling. In
        # case the user edits the MO later on and sets some consumed quantity on those, we do not
        # want the move lines to be canceled.
        (self.move_raw_ids | self.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })
        #Henry
        if self.date_finished:
            return
        else:
            return self.write({'date_finished': fields.Datetime.now()})
    def action_write_date_finished_in_done(self):
        exito=self.write_date_finished()
        if exito:
            mensaje = "Se Actualizo la Fecha Final en toda la Producción."
            message_id = self.env['sd.message.wizard'].create({'message': mensaje})
            return {
                'name': 'Proceso Exitoso!!',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'sd.message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }