# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, tools
import pytz
from odoo.exceptions import AccessError, UserError, ValidationError

class posOrderInheritCancel(models.Model):
    _inherit = "pos.order"
    state_session = fields.Selection("pos.session", related='session_id.state')
    # funcion action_view_cancel_wizard
    # modelo trasnsitorio pos.order.wizard
    # id de la pedido de punto de venta
    # mostrara el mensaje de estas seguro que desea continuar?
    #dos botones -> continuar -> cancelar
    # continuar= action_pos_order_cancel(self):
    # vals = super(posOrderInheritCancel, self).action_pos_order_cancel()
    # picking = self.picking_id
    # if picking:
    #     print("entro al if")
    #     picking.action_cancel()
    # return vals
    def get_account_move(self, selector):
        asientoSession = self.env["account.move"].search([('ref', '=', selector),
                                                          ('state', '=', 'posted')])
        return asientoSession
    def action_pos_order_cancel(self):
        grupo_cancel = self.env['res.users'].has_group('sd_pos_cancel_v13.sd_group_encargado_cancelar')
        if grupo_cancel:
            vals = super(posOrderInheritCancel, self).action_pos_order_cancel()
            picking = self.picking_id
            session = self.session_id
            payment_ids = self.payment_ids
            order_ids = session.order_ids
            factura = self.account_move
            fecha_sesion = session.stop_at

            if payment_ids:
                for payment_id in payment_ids:
                    payment_id.write({
                        'amount': 0
                    })

            if picking:
                picking.action_cancel()

            if factura:
                if factura.state == 'draft':
                    factura.button_cancel()
                elif factura.state == 'posted':
                    factura.button_draft()
                    factura.button_cancel()
            if session.state == 'closed':
                session.move_id.button_cancel()
                pagoSession = self.env["account.payment"].search([('communication', '=', session.name),
                                                                  ('state', '=', 'reconciled')])
                pagoSession.cancel()
                pagoSession.write({'communication': session.name+'cancelado'})
                asientoSession = self.get_account_move(session.name)
                asientoSession.button_cancel()
                session.write({'state': 'opened'})
                session.write({'stop_at': fecha_sesion})
                session.action_pos_session_closing_control()

                #fecha anterior usada en los asientos cancelados
                user_tz = self.env.user.tz
                local = pytz.timezone(user_tz)
                date_asiento = (pytz.utc.localize(fecha_sesion).astimezone(local)).date()
                asientoNewSession = self.get_account_move(session.name)
                asientoNewSession.write({'date': date_asiento})
                if order_ids:
                    for order_id in order_ids:
                        asiento_shop = self.get_account_move(order_id.name)
                        asiento_shop.write({'date': date_asiento})
        else:
            raise UserError(_('Usted no cuenta con los permisos para cancelar. \n '
                              'Contacte a su administrador de sistema.'))
        return vals

    # def refactor_statements(self, statement):
    #     if statement.

