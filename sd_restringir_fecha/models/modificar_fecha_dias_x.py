from odoo import models, fields,api, _
import datetime
import pytz
# from odoo.tools import date_utils
# from tzlocal import get_localzone
class FechaFactura(models.Model):
    _name = 'date.day.modify'
    _description = 'fecha factura'

    name = fields.Char(string ="Nombre ")
    campo_dias = fields.Integer(string="número de Dias ")

#                           Modulo de VENTAS

class InheritSale(models.Model):
    _inherit = "sale.order"


    # cada vez que exista un tipo de cambio en el campo fecha cotizacion hara la siguiente funcion

    @api.onchange('date_order')
    def modificar_fecha_Factura(self):
        # first_day = date_utils.start_of(self.date_order, 'day')
        # last_day = date_utils.end_of(self.date_order, 'day')
        if self.date_order:
            user_tz = self.env.user.tz
            local = pytz.timezone(user_tz)
            fecha_local = pytz.utc.localize(self.date_order).astimezone(local)
            fecha_Actual = pytz.utc.localize(fields.Datetime.now()).astimezone(local)
            fecha_date_Actual = fecha_Actual.date()
            fecha_entrada=fecha_local.date()

            # obtenemos los grupos en los que se encuentra el usuario
            grupo_todos=self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_all')
            #print("grupo_todo",grupo_todos)
            grupo_x_dias=self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_x_day')

            # obtenemos el # de dias que puede ingresar fecha antes o despues de la fecha actual
            dia_obj = self.env['date.day.modify'].search([])
            dias = dia_obj.mapped('campo_dias')
            #print("dia ",dias[0])
            #dias atras que esta permitida para dicho usuario
            fecha_dias_atras = fecha_date_Actual - datetime.timedelta(days=dias[0])
            #preguntamos si esta en el grupo de modificacion x dias
            if grupo_x_dias:
                if fecha_dias_atras <= fecha_entrada:
                    if not fecha_entrada <= fecha_date_Actual:
                        self.date_order = ""
                        return {
                            'warning': {
                                'message': _(
                                    f"Usted no tiene permiso para modificar una fecha mayor a la actual: {fecha_date_Actual}. ")
                            }
                        }
                else:
                    self.date_order = ""
                    return {
                        'warning': {
                            'message': _(
                                f"Usted no tiene permiso para modificar la fecha mas de {dias[0]} dias atras.")
                        }
                    }
            elif grupo_todos:
                print('Print cualquier fecha')
                # if not fecha_entrada <= fecha_date_Actual:
                #     self.date_order = ""
                #     return {
                #         'warning': {
                #             'message': _(
                #                 f"Usted no tiene permiso para modificar una fecha mayor a la actual: {fecha_date_Actual}. ")
                #         }
                #     }

#                       Modulo de Compra

class InheritPurchase(models.Model):
    _inherit = "purchase.order"

    # cada vez que exista un tipo de cambio en el campo fecha orden hara la siguiente funcion

    @api.onchange('date_order')
    def modificar_fecha_Factura(self):
        if self.date_order:
            # obtenemos la fecha de entrada
            user_tz = self.env.user.tz
            local = pytz.timezone(user_tz)
            fecha_local = pytz.utc.localize(self.date_order).astimezone(local)
            fecha_Actual = pytz.utc.localize(fields.Datetime.now()).astimezone(local)
            fecha_date_Actual = fecha_Actual.date()
            fecha_entrada = fecha_local.date()

            # obtenemos los grupos en los que se encuentra el usuario
            grupo_todos=self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_all')
            # print("grupo_todo",grupo_todos)
            grupo_x_dias = self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_x_day')

            # obtenemos el # de dias que puede ingresar fecha antes o despues de la fecha actual
            dia_obj = self.env['date.day.modify'].search([])
            dias = dia_obj.mapped('campo_dias')
            # obtenmos la fecha dias adelante y atras que esta permitida para dicho usuario
            fecha_dias_adelante = fecha_date_Actual + datetime.timedelta(days=dias[0])
            fecha_dias_atras = fecha_date_Actual - datetime.timedelta(days=dias[0])

            # preguntamos si esta en el grupo de modificacion x dias
            if grupo_x_dias:
                if fecha_dias_atras <= fecha_entrada:
                    if not fecha_entrada <= fecha_date_Actual:
                        self.date_order = ""
                        return {
                            'warning': {
                                'message': _(
                                    f"Usted no tiene permiso para modificar una fecha mayor a la actual: {fecha_date_Actual}. ")
                            }
                        }
                else:
                    self.date_order = ""
                    return {
                        'warning': {
                            'message': _(
                                f"Usted no tiene permiso para modificar la fecha {dias[0]} dias adelante o atras.")
                        }
                    }
            elif grupo_todos:
                print('Print cualquier fecha')
                # if not fecha_entrada <= fecha_date_Actual:
                #     self.date_order = ""
                #     return {
                #         'warning': {
                #             'message': _(
                #                 f"Usted no tiene permiso para modificar una fecha mayor a la actual: {fecha_date_Actual}. ")
                #         }
                #     }

#                   MODULO DE TRASNFERENCIA O STOCK

class InheritPicking(models.Model):
    _inherit = "stock.picking"

    @api.onchange('date_done')
    def modificar_fecha_efectiva(self):
        if self.date_done:
            user_tz = self.env.user.tz
            local = pytz.timezone(user_tz)
            fecha_local = pytz.utc.localize(self.date_done).astimezone(local)
            fecha_Actual = pytz.utc.localize(fields.Datetime.now()).astimezone(local)
            fecha_date_Actual = fecha_Actual.date()
            fecha_entrada = fecha_local.date()
            # obtenemos los grupos en los que se encuentra el usuario
            grupo_todos=self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_all')
            # print("grupo_todo",grupo_todos)
            grupo_x_dias = self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_x_day')

            # obtenemos el # de dias que puede ingresar fecha antes o despues de la fecha actual
            dia_obj = self.env['date.day.modify'].search([])
            dias = dia_obj.mapped('campo_dias')

            fecha_dias_atras = fecha_date_Actual - datetime.timedelta(days=dias[0])

            # preguntamos si esta en el grupo de modificacion x dias
            if grupo_x_dias:
                if fecha_dias_atras <= fecha_entrada:
                    if not fecha_entrada <= fecha_date_Actual:
                        self.date_done = ""
                        return {
                            'warning': {
                                'message': _(
                                    f"Usted no tiene permiso para modificar una fecha mayor a la actual: {fecha_date_Actual}. ")
                            }
                        }
                else:
                    self.date_done = ""
                    return {
                        'warning': {
                            'message': _(
                                f"Usted no tiene permiso para modificar la fecha {dias[0]} dias adelante o atras.")
                        }
                    }
            elif grupo_todos:
                print('Print cualquier fecha')
                # if not fecha_entrada <= fecha_date_Actual:
                #     self.date_done = ""
                #     return {
                #         'warning': {
                #             'message': _(
                #                 f"Usted no tiene permiso para modificar una fecha mayor a la actual: {fecha_date_Actual}. ")
                #         }
                #     }

    @api.onchange('scheduled_date')
    def modificar_fecha_prevista(self):
        if self.scheduled_date:
            user_tz = self.env.user.tz
            local = pytz.timezone(user_tz)
            fecha_local = pytz.utc.localize(self.scheduled_date).astimezone(local)
            fecha_Actual = pytz.utc.localize(fields.Datetime.now()).astimezone(local)
            fecha_date_Actual = fecha_Actual.date()
            fecha_entrada = fecha_local.date()
            # obtenemos los grupos en los que se encuentra el usuario
            grupo_todos = self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_all')
            # print("grupo_todo",grupo_todos)
            grupo_x_dias = self.env['res.users'].has_group('sd_restringir_fecha.group_modify_date_x_day')

            # obtenemos el # de dias que puede ingresar fecha antes o despues de la fecha actual
            dia_obj = self.env['date.day.modify'].search([])
            dias = dia_obj.mapped('campo_dias')

            fecha_dias_atras = fecha_date_Actual - datetime.timedelta(days=dias[0])

            # preguntamos si esta en el grupo de modificacion x dias
            if grupo_x_dias:
                if fecha_dias_atras <= fecha_entrada:
                    if not fecha_entrada <= fecha_date_Actual:
                        self.scheduled_date = ""
                        return {
                            'warning': {
                                'message': _(
                                    f"Usted no tiene permiso para modificar una fecha mayor a la actual: {fecha_date_Actual}. ")
                            }
                        }
                else:
                    self.scheduled_date = ""
                    return {
                        'warning': {
                            'message': _(
                                f"Usted no tiene permiso para modificar la fecha {dias[0]} dias adelante o atras.")
                        }
                    }
            elif grupo_todos:
                print('Print cualquier fecha')
                # if not fecha_entrada <= fecha_date_Actual:
                #     self.scheduled_date = ""
                #     return {
                #         'warning': {
                #             'message': _(
                #                 f"Usted no tiene permiso para modificar una fecha mayor a la actual: {fecha_date_Actual}. ")
                #         }
                #     }

