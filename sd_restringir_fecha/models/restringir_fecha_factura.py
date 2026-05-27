from odoo import models, fields,api, _
import datetime

class InheritAccount_move_restringir_fecha(models.Model):
    _inherit = "account.move"

    # cagar fecha factura por defecto usando onchange
    @api.onchange('invoice_date')
    def _onchange_invoice_date(self):
        res = super(InheritAccount_move_restringir_fecha, self)._onchange_invoice_date()
        if self.invoice_date:
            if not self.invoice_payment_term_id and (
                    not self.invoice_date_due or self.invoice_date_due < self.invoice_date):
                self.invoice_date_due = self.invoice_date
            self.date = self.invoice_date
            self._onchange_currency()
        else:
            self.invoice_date = fields.Date.today()
        return res

    @api.onchange('invoice_date')
    def modificar_fecha_Factura(self):
        if self.invoice_date:
            # obtenemos la fecha de entrada
            fecha_entrada = self.invoice_date

            grupo_todos = self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_all')
            grupo_x_dias = self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_x_day')

            # obtenemos el # de dias que puede ingresar fecha antes o despues de la fecha actual
            dia_obj = self.env['date.day.modify'].search([])
            dias = dia_obj.mapped('campo_dias')
            fecha_date_Actual = fields.Date.today()
            fecha_dias_atras = fecha_date_Actual - datetime.timedelta(days=dias[0])
            # preguntamos si esta en el grupo de modificacion x dias
            if grupo_x_dias:
                if fecha_dias_atras <= fecha_entrada:
                    if not fecha_entrada <= fecha_date_Actual:
                        self.invoice_date = ""
                        return {
                            'warning': {
                                'message': _(
                                    f"Usted no tiene permiso para colocar una fecha mayor a la actual: {fecha_date_Actual}. ")
                            }
                        }
                else:
                    self.invoice_date = ""
                    return {
                        'warning': {
                            'message': _(
                                f"Usted no tiene permiso para colocar una fecha mas de {dias[0]} dias atras.")
                        }
                    }
            elif grupo_todos:
                print('Print cualquier fecha')
                # if not fecha_entrada <= fecha_date_Actual:
                #     self.invoice_date = ""
                #     return {
                #         'warning': {
                #             'message': _(
                #                 f"Usted no tiene permiso para colocar una fecha mayor a la actual: {fecha_date_Actual}. ")
                #         }
                #     }
            else:
                if not fecha_date_Actual == fecha_entrada:
                    self.invoice_date = ""
                    return {
                        'warning': {
                            'message': _(
                                f"No tiene permiso para colocar una fecha mayor o menor que: {fecha_date_Actual}. ")
                        }
                    }
