from odoo import models, fields,api, _
import datetime
import pytz
from odoo.tools import date_utils
class inherit_payment_register(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.onchange('payment_date')
    def modificar_fecha_Factura(self):
        if self.payment_date:
            user_tz = self.env.user.tz
            local = pytz.timezone(user_tz)
            # obtenemos la fecha de entrada
            fecha_entrada = self.payment_date

            grupo_todos = self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_all')
            grupo_x_dias = self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_x_day')

            # obtenemos el # de dias que puede ingresar fecha antes o despues de la fecha actual
            dia_obj = self.env['date.day.modify'].search([])
            dias = dia_obj.mapped('campo_dias')
            fecha_Actual = pytz.utc.localize(fields.Datetime.now()).astimezone(local)
            fecha_date_Actual = fecha_Actual.date()
            fecha_dias_atras = fecha_date_Actual - datetime.timedelta(days=dias[0])
            # preguntamos si esta en el grupo de modificacion x dias
            if grupo_x_dias:
                if fecha_dias_atras <= fecha_entrada:
                    if not fecha_entrada <= fecha_date_Actual:
                        self.payment_date = ""
                        return {
                            'warning': {
                                'message': _(
                                    f"Usted no tiene permiso para colocar una fecha mayor a la actual: {fecha_date_Actual}. ")
                            }
                        }
                else:
                    self.payment_date = ""
                    return {
                        'warning': {
                            'message': _(
                                f"Usted no tiene permiso para colocar una fecha mas de {dias[0]} dias atras.")
                        }
                    }
            elif grupo_todos:
                print('Print cualquier fecha')
                # if not fecha_entrada <= fecha_date_Actual:
                #     self.payment_date = ""
                #     return {
                #         'warning': {
                #             'message': _(
                #                 f"Usted no tiene permiso para colocar una fecha mayor a la actual: {fecha_date_Actual}. ")
                #         }
                #     }
            else:
                if not fecha_date_Actual == fecha_entrada:
                    self.payment_date = ""
                    return {
                        'warning': {
                            'message': _(
                                f"No tiene permiso para colocar una fecha mayor o menor que: {fecha_date_Actual}. ")
                        }
                    }
class inherit_account_payment(models.Model):
    _inherit = 'account.payment'

    @api.onchange('payment_date')
    def modificar_fecha_Factura(self):
        # user_tz = self.env.user.tz
        # local = pytz.timezone(user_tz)
        # print(user_tz, 'user tz', local)
        # new_date = self.payment_date.strftime('%d/%m/%Y %H:%M%S')
        if self.payment_date:
            user_tz = self.env.user.tz
            local = pytz.timezone(user_tz)
            # obtenemos la fecha de entrada
            fecha_entrada = self.payment_date

            grupo_todos = self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_all')
            grupo_x_dias = self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_x_day')

            # obtenemos el # de dias que puede ingresar fecha antes o despues de la fecha actual
            dia_obj = self.env['date.day.modify'].search([])
            dias = dia_obj.mapped('campo_dias')
            fecha_Actual = pytz.utc.localize(fields.Datetime.now()).astimezone(local)
            fecha_date_Actual = fecha_Actual.date()
            fecha_dias_atras = fecha_date_Actual - datetime.timedelta(days=dias[0])
            # preguntamos si esta en el grupo de modificacion x dias
            if grupo_x_dias:
                if fecha_dias_atras <= fecha_entrada:
                    if not fecha_entrada <= fecha_date_Actual:
                        self.payment_date = ""
                        return {
                            'warning': {
                                'message': _(
                                    f"Usted no tiene permiso para colocar una fecha mayor a la actual: {fecha_date_Actual}. ")
                            }
                        }
                else:
                    self.payment_date = ""
                    return {
                        'warning': {
                            'message': _(
                                f"Usted no tiene permiso para colocar una fecha mas de {dias[0]} dias atras.")
                        }
                    }
            elif grupo_todos:
                print('Print cualquier fecha')
                # if not fecha_entrada <= fecha_date_Actual:
                #     self.payment_date = ""
                #     return {
                #         'warning': {
                #             'message': _(
                #                 f"Usted no tiene permiso para colocar una fecha mayor a la actual: {fecha_date_Actual}. ")
                #         }
                #     }
            else:
                if not fecha_date_Actual == fecha_entrada:
                    self.payment_date = ""
                    return {
                        'warning': {
                            'message': _(
                                f"No tiene permiso para colocar una fecha mayor o menor que: {fecha_date_Actual}. ")
                        }
                    }




