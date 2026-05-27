# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import pytz
from odoo.exceptions import Warning, UserError
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError
import datetime


class AutomatedPurchaseOrder(models.Model):
    _name = "automated.purchase"

    name = fields.Char(string="Nombre")
    payment_journal = fields.Many2one("account.journal", string="Diario de Pago",
                                      domain=[['type', 'in', ['bank', 'cash']]])
    work_order_process_id_p2 = fields.Many2one('automated.purchase', string="Flujo de Venta Empresa 2")
    i_impuestos_flujo2 = fields.Many2many('account.tax', string="Impuestos",
                                          domain="[('company_id', '=', company_id), ('type_tax_use', 'in', ['purchase'])]",)
    # adiccionados
    # controlar la secuencia
    @api.model
    def _filtrar_secuencia(self):
        nuevo_objeto_secuencia = []
        objetos_secuencia = self.env['ir.sequence'].search([])
        if objetos_secuencia:
            for secuencia in objetos_secuencia:
                if secuencia.code:
                    cadena_secuencia = ''
                    bandera_primer_punto = False
                    for letra in secuencia.code:
                        if bandera_primer_punto:
                            cadena_secuencia = cadena_secuencia + letra
                            if len(cadena_secuencia) >= 14:
                                if cadena_secuencia == 'purchase.order':
                                    nuevo_objeto_secuencia.append(secuencia.id)
                                    break
                                else:
                                    break
                        else:
                            if letra == '.':
                                bandera_primer_punto = True
        return nuevo_objeto_secuencia

    @api.model
    def _filtrar_secuencia_quotation(self):
        nuevo_objeto_secuencia = []
        objetos_secuencia = self.env['ir.sequence'].search([])
        if objetos_secuencia:
            for secuencia in objetos_secuencia:
                if secuencia.code:
                    cadena_secuencia = ''
                    bandera_primer_punto = False
                    for letra in secuencia.code:
                        if bandera_primer_punto:
                            cadena_secuencia = cadena_secuencia + letra
                            if len(cadena_secuencia) >= 18:
                                if cadena_secuencia == 'purchase.quotation':
                                    nuevo_objeto_secuencia.append(secuencia.id)
                                    break
                                else:
                                    break
                        else:
                            if letra == '.':
                                bandera_primer_punto = True
        return nuevo_objeto_secuencia

    st_secuencia = fields.Many2one('ir.sequence', string="Secuencia Compra")#domain=lambda self: [('id', 'in', self._filtrar_secuencia())]
    st_entregar_a = fields.Many2one('stock.picking.type', string="Entregar a", domain=[['code','in',['incoming']]])
    st_secuencia_quotation = fields.Many2one('ir.sequence', string="Secuencia Presupuesto")#domain=lambda self: [('id', 'in', self._filtrar_secuencia_quotation())]

    type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
    ], readonly=True, index=True, change_default=True,
        default=lambda self: self._context.get('type', 'out_invoice'),
        track_visibility='always')
    company_id = fields.Many2one('res.company', string='Compañia')
    purchase_journal = fields.Many2one("account.journal", string="Diario de Compra",
                                       domain="[('type', '=','purchase')]")

    validation_order = fields.Boolean("Validar Orden")
    validation_picking = fields.Boolean("Validar Recepcion",default="True")
    force_transfer = fields.Boolean("Forzar trasferencia, incluso si no esta disponible.")
    create_incoice = fields.Boolean("Crear Factura")
    validate_invoice = fields.Boolean("Validar Factura")
    register_payment = fields.Boolean("Registrar Pago")
    # force_invoice = fields.Boolean("Forzar Fecha de la Factura")


    control_policy = fields.Selection(
        [('purchase', 'En cantidades pedidas'),
         ('receive', 'Sobre cantidades recibidas'),
         ], string='Politica de Control', required=True)
    # Adicionar
    sd_is_numero_recibo = fields.Boolean(string='Nro Recibo', default=False)
    sd_is_numero_factura = fields.Boolean(string='Nro Factura', default=False)
    sd_is_numero_importacion = fields.Boolean(string='Nro Importación', default=False)
    sd_is_ref =fields.Boolean(string='Nota de Entrega', default=False)
    sd_is_facturacion =fields.Boolean(string='es Facturación', default=False)

    #IMPUESTOS POR PAGAR
    sd_is_impuesto_por_pagar = fields.Boolean(string='Impuesto por Pagar', default=False)
    sd_automated_purchase_tax_ids = fields.One2many('automated.purchase.tax','sd_automated_id',string='Impuesto por pagar')

    @api.onchange('validate_invoice', 'register_payment')
    def depends_force(self):
        # if self.force_invoice == True:
        #     self.validate_invoice = True

        if self.validate_invoice == True:
            self.create_incoice = True

        if self.register_payment == True:
            self.validate_invoice = True

    @api.onchange('force_transfer', 'validation_picking')
    def depends_transfer(self):
        if self.force_transfer == True:
            self.validation_picking = True

        if self.validation_picking == True:
            self.validation_order = True

    @api.onchange('create_incoice')
    def depends_invoice(self):
        if self.create_incoice == True:
            self.validation_order = True
            self.validation_picking = True
            self.force_transfer = True
class AutomatedPurchaseOrderTax(models.Model):
    _name = 'automated.purchase.tax'

    sd_automated_id = fields.Many2one('automated.purchase')
    name = fields.Char(string='Nombre')
    sd_porcentaje = fields.Float('%')
    sd_account_ids = fields.One2many('automated.purchase.account','sd_automated_tax_id',string='Cuentas por Pagar')
    journal_id = fields.Many2one('account.journal',string='Diario')
class AutomatedPurchaseOrderAccount(models.Model):
    _name = 'automated.purchase.account'
    sd_automated_tax_id = fields.Many2one('automated.purchase.tax')
    sd_account_id = fields.Many2one('account.account', 'Cuenta por Pagar')
    name = fields.Char(string='Nombre')
    sd_porcentaje = fields.Float('%')

class InheritPartner(models.Model):
    _inherit = "res.partner"

    is_automated_compra = fields.Boolean(string="Flujo de Trabajo Automatizado",default="True")
    work_process_id_compra = fields.Many2one("automated.purchase", string="Tipo de Compra")


class InheritPurchase(models.Model):
    _inherit = "purchase.order"

    is_related = fields.Boolean(related="partner_id.is_automated_compra")
    work_process_order_id = fields.Many2one("automated.purchase", string="Tipo de Compra")
    sd_origen_compra_id = fields.Many2one('purchase.order', string="Compra origen")
    sd_compra_contable = fields.Many2one('purchase.order', string="Compra Otra compañia")
    st_orden_cancelada = fields.Boolean(default=False)
    # para agregar recibo y factura
    sd_numero_recibo = fields.Char(string='Nro Recibo')
    sd_numero_factura = fields.Char(string='Nro Factura')
    sd_numero_importacion = fields.Char(string='Nro Importación')
    sd_is_nro_recibo = fields.Boolean(related='work_process_order_id.sd_is_numero_recibo')
    sd_is_nro_factura = fields.Boolean(related='work_process_order_id.sd_is_numero_factura')
    sd_is_numero_importacion = fields.Boolean(related='work_process_order_id.sd_is_numero_importacion')
    sd_is_facturacion = fields.Boolean(related='work_process_order_id.sd_is_facturacion')
    # campo referencia entrega
    sd_ref_entrega = fields.Char(string='Nota de Entrega')
    sd_is_ref = fields.Boolean(related='work_process_order_id.sd_is_ref')

    # FACTURACION EN LINEA Y FUERA DE LINEA
    fcb_es_factura_compra = fields.Boolean(string='Facturación Compra',copy=False)
    fcb_autorizacion_compra_order = fields.Char(string="Numero de Autorizacion",copy=False)
    fcb_codigo_control_compra_order = fields.Char(string="Codigo de Control",copy=False)
    fcb_numero_dim_order = fields.Char(string="Numero de Declaracion de Importacion",copy=False)

    sd_numero_dui = fields.Char(string="DUI")
    sd_codigo_aduana = fields.Selection([
        ('071', '071 Agencia Exterior Matarani'),
        ('072', '072 Agencia Exterior Arica'),
        ('073', '073 Agencia Exterior Matarani-Ilo'),
        ('101', '101 Interior Sucre'),
        ('102', '102 Especializada Interior Sucre'),
        ('111', '111 Aeropuerto Sucre'),
        ('201', '201 Interior La Paz'),
        ('202', '202 Especializada Interior La Paz'),
        ('211', '211 Aeropuerto El Alto'),
        ('221', '221 Frontera Chara¤a'),
        ('231', '231 Zona Franca Comercial El Alto'),
        ('232', '232 Zona Franca Industrial El Alto'),
        ('233', '233 Zona Franca Comercial Desaguadero'),
        ('234', '234 Zona Franca Industrial Patacamaya'),
        ('235', '235 Zona Franca Comercial Patacamaya'),
        ('241', '241 Frontera Desaguadero'),
        ('242', '242 Frontera Kasani'),
        ('243', '243 CEBAF Desaguadero'),
        ('244', '244 Frontera Puerto Acosta'),
        ('261', '261 Postal La Paz'),
        ('301', '301 Interior Cochabamba'),
        ('302', '302 Especializada Interior Cochabamba'),
        ('311', '311 Aeropuerto Cochabamba'),
        ('331', '331 Zona Franca Comercial Cochabamba'),
        ('332', '332 Zona Franca Industrial Cochabamba'),
        ('361', '361 Postal Cochabamba'),
        ('401', '401 Interior Oruro'),
        ('402', '402 Especializada Interior Oruro'),
        ('421', '421 Frontera Pisiga'),
        ('422', '422 Frontera Tambo Quemado'),
        ('431', '431 Zona Franca Comercial Oruro'),
        ('432', '432 Zona Franca Industrial Oruro'),
        ('501', '501 Interior Potosi'),
        ('502', '502 Especializada Interior Potosi'),
        ('521', '521 Frontera Villaz¢n'),
        ('522', '522 ACI Villaz¢n'),
        ('531', '531 Zona Franca Comercial Villaz¢n'),
        ('542', '542 Frontera Apacheta/Hito Cajones'),
        ('543', '543 Frontera Avaroa'),
        ('601', '601 Interior Tarija'),
        ('602', '602 Especializada Interior Tarija'),
        ('611', '611 Aeropuerto Tarija'),
        ('621', '621 Frontera Yacuiba'),
        ('622', '622 Frontera Picada Sucre'),
        ('623', '623 ACI Yacuiba'),
        ('631', '631 Zona Franca Comercial Yacuiba'),
        ('641', '641 Frontera Bermejo'),
        ('642', '642 ACI Bermejo'),
        ('643', '643 Frontera Ca¤ada Oruro'),
        ('701', '701 Interior Santa Cruz'),
        ('702', '702 Especializada Interior Santa Cruz'),
        ('711', '711 Aeropuerto Viru-Viru'),
        ('712', '712 Aeropuerto Puerto Suarez'),
        ('721', '721 Frontera Puerto Suarez'),
        ('722', '722 Frontera Arroyo Concepcion'),
        ('723', '723 Punto de Control "El Faro"'),
        ('731', '731 Zona Franca Comercial Pto. Aguirre'),
        ('732', '732 Zona Franca Comercial Santa Cruz'),
        ('733', '733 Zona Franca Comercial San Matias'),
        ('734', '734 Zona Franca Comercial Pto. Suarez'),
        ('735', '735 Zona Franca Comercial Winner'),
        ('736', '736 Zona Franca Industrial Pto. Suarez'),
        ('737', '737 Zona Franca Winner'),
        ('738', '738 Zona Franca Industrial Santa Cruz'),
        ('741', '741 Frontera San Matias'),
        ('743', '743 Frontera San Vicente'),
        ('751', '751 Fluvial Puerto Jennefer'),
        ('752', '752 Punto de Control "El Faro"'),
        ('761', '761 Postal Santa Cruz'),
        ('801', '801 Interior Trinidad'),
        ('831', '831 Zona Franca Comercial Guayaramerin'),
        ('841', '841 Frontera Guayaramerin'),
        ('842', '842 Punto de controL(ACI)Guajara-Mirim'),
        ('862', '862 Postal Trinidad'),
        ('911', '911 Aeropuerto Cobija'),
        ('921', '921 Frontera Cobija'),
        ('931', '931 Zona Franca Comercial e Ind.Cobija'), ], string='Aduana Destino')

    fcb_numero_factura = fields.Char(string="Numero de Factura",copy=False)
    fcb_cuf = fields.Char(string="CUF",copy=False)
    fcb_link = fields.Char(string='URL',copy=False)
    fcb_tipo_compra_order = fields.Selection([
        ('compra_interno_gravadas', 'Compras para mercado interno con destino a actividades gravadas'),
        ('compra_interno_no_gravadas', 'Compras para mercado interno con destino a actividades no gravadas,'),
        ('compra_proporcionalidad', 'Compras sujetas a proporcionalidad'),
        ('compra_exportaciones', 'Compras para exportaciones'),
        ('compra_interno_exportaciones', 'Compras tanto para el mercado interno como para exportaciones'),
    ],
        string='Factura de Compras',copy=False)

    @api.depends('sd_automated_purchase_tax_id','order_line.price_total')
    def calcular_impuesto_retencion(self):
        for order in self:
            order.sd_amount_total_impuesto_retencion = 0
            order.sd_impuesto_retencion = 0
            if order.sd_automated_purchase_tax_id:
                porcentaje = 1 - (order.sd_automated_purchase_tax_id.sd_porcentaje/100)
                if order.amount_total != 0:
                    order.sd_impuesto_retencion = (order.amount_total /porcentaje) * (order.sd_automated_purchase_tax_id.sd_porcentaje/100)
                    order.sd_amount_total_impuesto_retencion = order.amount_total /porcentaje

    #IMPUESTOS IT Y IUE
    sd_is_impuesto_por_pagar = fields.Boolean(related='work_process_order_id.sd_is_impuesto_por_pagar')
    sd_automated_purchase_tax_id = fields.Many2one('automated.purchase.tax', string='Impuesto Retención',domain="[('sd_automated_id', '=', work_process_order_id)]")
    sd_impuesto_retencion = fields.Monetary(string='Imp. Ret.',store=True, compute='calcular_impuesto_retencion',default=0)
    sd_amount_total_impuesto_retencion = fields.Monetary(string='Total + Impuesto Ret.', store=True, compute='calcular_impuesto_retencion',default=0)
    sd_register_payment = fields.Boolean("Registrar Pago",related='work_process_order_id.register_payment')
    sd_glosa_payment = fields.Char('Glosa del Pago')
    @api.onchange('fcb_autorizacion_compra_order')
    def maximo_caracteres(self):

        caracteres = self.fcb_autorizacion_compra_order
        diccionario_numerico = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
        if caracteres:
            for i in caracteres:
                if not i in diccionario_numerico:
                    self.fcb_autorizacion_compra_order = ''
                    return {
                        'warning': {
                            'message': _(
                                f'Se permiten solo caracteres numérico en el campo: "Fecha de Activación", porfavor vuelva a intentarlo!!. ')
                        }
                    }
    @api.onchange('work_process_order_id')
    def _controlar_flujo_de_trabajo_compra(self):
        if self.work_process_order_id:
            self.picking_type_id = self.work_process_order_id.st_entregar_a

    @api.onchange('picking_type_id')
    def _controlar_almacen(self):
        if self.picking_type_id:
            #print("almacen id ", self.picking_type_id.id)
            if self.work_process_order_id:
                if not self.picking_type_id.id == self.work_process_order_id.st_entregar_a.id:
                    #print("no son iguales")
                    return {
                        'warning': {
                            'message': _(
                                'El campo Flujo de Trabajo y Entregar a son de distintos .')
                        }
                    }

    # Se Hereda el metodo button_approve de modulo purchase(purchase.order) para modificar
    # la fecha confimar: date_approve

    def button_approve(self, force=False):
        date_order = self.date_order
        self.write({'state': 'purchase', 'date_approve': date_order})#fields.Datetime.now()})
        self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
        return {}

    @api.onchange("partner_id")
    def change_workflow(self):
        if self.partner_id.work_process_id_compra:
            self.work_process_order_id = self.partner_id.work_process_id_compra.id

    def action_automate(self):
        # Creamos una variable que contendra la fecha ingresada por el formulario compra
        date_order = self.date_order
        user_tz = self.env.user.tz
        local = pytz.timezone(user_tz)
        date_order_factura_pago = (pytz.utc.localize(date_order).astimezone(local)).date()

        self.sd_numero_dui = self.generar_dui()

        if self.work_process_order_id:
            self.add_parametros(date_order)

            if self.work_process_order_id.validation_order:
                self.button_confirm()

            if self.work_process_order_id.create_incoice:

                vals = self.denifinir_vals(date_order_factura_pago)
                self.validar_lines_purchase(vals, date_order_factura_pago)
            self.order_process(date_order, date_order_factura_pago)

            if self.work_process_order_id.work_order_process_id_p2:
                self._duplicate_purchase_multicompany()
            if self.sd_is_impuesto_por_pagar and self.sd_automated_purchase_tax_id:
                self.crear_asiento_retencion_impuesto(date_order_factura_pago)
        else:
            raise Warning(('El campo Tipo de Compra es obligatorio.'))

    def validar_lines_purchase(self, vals, date_order_factura_pago):
        account_inv_obj = self.env['account.move']
        res = account_inv_obj.create(vals)
        po_lines = self.order_line
        new_lines = self.env['account.move.line']
        new_lines = []
        for line in po_lines.filtered(lambda l: not l.display_type):
            new_lines.append((0, 0, line._prepare_account_move_line(res)))
        res.write({
            'invoice_line_ids': new_lines,
            'purchase_id': self.id,
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
                    'communication': res.name +' '+self.sd_glosa_payment if self.sd_glosa_payment else ' ',
                    'invoice_ids': [(6, 0, [res.id])]
                })

                sequence_code = 'account.payment.vendor.bill'
                payment_order.write({

                    'name': self.env['ir.sequence'].with_context(
                        ir_sequence_date=payment_order.payment_date).next_by_code(sequence_code),

                })

                res.reconciled = True
                res.action_invoice_paid()
                payment_order.post()



            elif self.work_process_order_id.validate_invoice == True:  # self.work_process_order_id.force_invoice == True
                res.action_post()
                # escribir fecha apuntes contables
                objeto_move_line = self.env['account.move.line'].search([('move_id', '=', res.id)])
                if objeto_move_line:
                    for account_move_line in objeto_move_line.filtered(lambda l:l.exclude_from_invoice_tab == True):
                        account_move_line.write({
                            # 'date_maturity': date_order_factura_pago,
                            'name':'Factura del Proveedor '+res.name + ' Compra: '+self.name+'\n' + self.partner_ref if self.partner_ref else ' '
                        })

            else:
                pass

    def order_process(self, date_order, date_order_factura_pago):
        for order in self:
            picking_obj = self.env['stock.picking'].search([('origin', '=', order.name)])
            if self.work_process_order_id.validation_picking == True or self.work_process_order_id.force_transfer == True:
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
                        objeto_account_move = self.env['account.move'].search([('stock_move_id', '=', stock_move.id)])
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
                                    "UPDATE public.stock_valuation_layer SET create_date=%s WHERE id=%s ", (parametros))
                # escribir fecha Movimiento de productos
                objeto_stock_move_line = self.env['stock.move.line'].search([('picking_id', '=', picking_obj.id)])
                if objeto_stock_move_line:
                    for stock_move_line in objeto_stock_move_line:
                        stock_move_line.write({
                            'date': date_order,
                        })

            else:
                return
    def add_parametros(self, date_order):
        for line in self.order_line:
            line.product_id.sudo().write({
                'purchase_method':self.work_process_order_id.control_policy
            })
            # parametros = []
            # parametros.append(self.work_process_order_id.control_policy)
            # parametros.append(line.product_id.id)
            # self.env.cr.execute("UPDATE public.product_template SET purchase_method=%s WHERE id=%s ", (parametros))
            # escribir fecha orden de linea
            line.write({'date_planned': date_order})

    def denifinir_vals(self, date_order_factura_pago):
        vals = {
            'type': 'in_invoice',
            'invoice_origin': self.name,
            'purchase_id': self.id,
            'partner_id': self.partner_id.id,
            # ingresamo el diario , la fecha factura Y LA FECHA CONTABLE
            'journal_id': self.work_process_order_id.purchase_journal.id,
            'invoice_date': date_order_factura_pago,
            'date': date_order_factura_pago,
            'invoice_payment_term_id':self.payment_term_id.id,
            'ref': self.partner_ref if self.partner_ref else '',
            'currency_id': self.currency_id.id,
            'sd_codigo_aduana': self.sd_codigo_aduana,
            'sd_numero_dui': self.sd_numero_dui,
        }
        # Numero de recibo
        if self.sd_is_nro_recibo:
            existe_recibo = True
            if self.work_process_order_id.validate_invoice:
                existe_recibo = True if self.sd_numero_recibo else False
            vals.update({
                'sd_numero_recibo_purchase': self.sd_numero_recibo,
                'sd_is_numero_recibo_purchase': existe_recibo,
            })
        # NUemro de factura
        if self.sd_is_nro_factura:
            existe_factura = True
            if self.work_process_order_id.validate_invoice:
                existe_factura = True if self.sd_numero_factura else False
            vals.update({
                'sd_numero_factura_purchase': self.sd_numero_factura,
                'sd_is_numero_factura_purchase': existe_factura,
            })
        # referencia Entrega
        if self.sd_is_ref:
            existe_factura = True
            if self.work_process_order_id.validate_invoice:
                existe_factura = True if self.sd_ref_entrega else False
            vals.update({
                'sd_ref_entrega': self.sd_ref_entrega,
                'sd_is_ref': existe_factura,
            })
        # Numero importacion
        if self.sd_is_numero_importacion:
            existe_importacion = True
            if self.work_process_order_id.validate_invoice:
                existe_importacion = True if self.sd_is_numero_importacion else False
            vals.update({
                'sd_nro_importacion': self.sd_numero_importacion,
                'sd_is_nro_importacion': existe_importacion,
            })
        if self.sd_is_facturacion:
            existe_importacion = True
            if self.work_process_order_id.validate_invoice:
                existe_importacion = True if self.sd_is_facturacion else False
            vals.update({
                'fcb_autorizacion_compra': self.fcb_autorizacion_compra_order,
                'fcb_codigo_control_compra': self.fcb_codigo_control_compra_order,
                'fcb_numero_dim': self.fcb_numero_dim_order,
                'fcb_tipo_compra': self.fcb_tipo_compra_order,
                'fcb_numero_factura': self.fcb_numero_factura,
                'fcb_link': self.fcb_link,
                'fcb_cuf': self.fcb_cuf,
                'fcb_es_factura_compra':self.fcb_es_factura_compra,
                
            })
        return vals
    #metoo para poder registrar los registrso en la compañia 2 david
    def _duplicate_purchase_multicompany(self):
       #todo David en la linea 184 se comenta porque al momento de querer validar la compra
       # no se puede registrar ya que el picking type pertenece a una compañia en especifico
        vals_c = self.get_vals_c()
        orders_2 = self.env['purchase.order'].sudo().create(vals_c)
        for lines in self.order_line:
            vals_c_line = self.get_vals_c_lines(lines, orders_2)
            self.env['purchase.order.line'].sudo().create(vals_c_line)

        orders_2.action_automate()

        orders_2.sd_origen_compra_id.update({
            "sd_compra_contable": orders_2.id
        })


    def get_vals_c(self):
        '''
               Esta función obtiene los valores que se necesitan para crear la compra doble
               Esta puede realizarse sin datos de entrada  .. by Franz
        '''
        vals_c = {
            'company_id': self.work_process_order_id.work_order_process_id_p2.company_id.id,
            'partner_id': self.partner_id.id,
            'partner_ref': self.partner_ref,
            'date_order': self.date_order,
            'work_process_order_id': self.work_process_order_id.work_order_process_id_p2.id,
            # 'picking_type_id': self.picking_type_id.id,
            'user_id': self.user_id.id,
            'sd_origen_compra_id': self.id,
        }
        return vals_c


    def get_vals_c_lines(self, lines, orders):
        '''
             Esta función obtiene los valores para crear las lineas de compra de detalle.
             solo necesita pasarles las lineas de las ordenes y la orden en general ... by Franz
        '''
        vals_c_line = {
            'company_id': orders.company_id.id,
            'order_id': orders.id,
            'name': lines.name,
            'product_qty': lines.product_qty,
            # 'qty_received': lines.qty_received,
            # 'qty_invoiced': lines.qty_invoiced,
            'product_id': lines.product_id.id,
            'price_unit': lines.price_unit,
            'product_uom': lines.product_uom.id,
            'taxes_id': self.sudo().work_process_order_id.work_order_process_id_p2.i_impuestos_flujo2.filtered(lambda x: x.company_id.id == self.work_process_order_id.work_order_process_id_p2.company_id.id),
            'date_planned': orders.date_order,
            # 'analytic_tag_ids': orders_2.analytic_tag_ids.ids,
        }
        return vals_c_line


    # Arreglar el duplicate y pasarle la fecha-Henry 2022
    def copy(self, vals=None):
        if self.date_order:
            vals = {'date_order': self.date_order}
            res = super(InheritPurchase, self).copy(vals)
        else:
            res = super(InheritPurchase, self).copy()
        return res
    def crear_asiento_retencion_impuesto(self,date_order):
        '''
        esta funcion tiene como objetivo generar un asiento para la retencion de impuesto al realizar la compra
        '''
        self.validar_datos_impuesto()
        self.ensure_one()
        move_lines = self._prepare_account_move_line(date_order)
        vals = {
                'ref': self.name +' - '+ self.sd_automated_purchase_tax_id.name,
                'journal_id': self.sd_automated_purchase_tax_id.journal_id.id,
                'company_id': self.company_id.id,
                'date': date_order,
                'type': 'entry',
                'invoice_origin': self.name,
                'line_ids': move_lines,
        }
        # 2) crear asiento contable
        account_move = self.env['account.move'].create(vals)
        # 4) Publicar Asiento contable
        if self.work_process_order_id.validate_invoice == True:
            account_move.action_post()
        self.update({
            'invoice_ids':[(4,account_move.id)],
            'invoice_count': self.invoice_count + len(account_move)
        })
    def _prepare_account_move_line(self,date_order):
        """ Ordernar las lineas contables """
        res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(date_order)]
        return res
    def _generate_valuation_lines_data(self,date_order):
        # Este método devuelve un diccionario para proporcionar un enlace de extensión fácil para modificar las líneas de valoración
        self.ensure_one()
        linea_move = []
        for line in self.order_line:
            total_impuesto_line = line.price_total/(1-(self.sd_automated_purchase_tax_id.sd_porcentaje/100))
            total_impuesto = 0
            for account_id in self.sd_automated_purchase_tax_id.sd_account_ids:
                debit_line_vals = {
                    'quantity': 1,
                    'name': self.name+': '+line.name,
                    'account_id':account_id.sd_account_id.id ,
                    'debit': 0.0,
                    'credit': total_impuesto_line * (account_id.sd_porcentaje /100),
                    'date':date_order,
                }
                linea_move.append(debit_line_vals)
                total_impuesto += total_impuesto_line * (account_id.sd_porcentaje /100)
            credit_line_vals = {
                'quantity': 1,
                'name': self.name+': '+line.name,
                'account_id': line.product_id.property_account_expense_id.id or line.product_id.categ_id.property_account_expense_categ_id.id,
                'debit': total_impuesto,
                'credit': 0.0,
                'date': date_order,
            }
            linea_move.append(credit_line_vals)

        rslt = linea_move
        return rslt
    def validar_datos_impuesto(self):
        if not self.sd_automated_purchase_tax_id.journal_id:
            raise Warning(('El Impuesto Retencion no cuenta con un Diario definido'))

        for account_id in self.sd_automated_purchase_tax_id.sd_account_ids:
            if not account_id.sd_account_id:
                raise Warning(('Cuenta por pagar no definida en el Impuesto Retencion'))

    def generar_dui(self):
        numero_dui = ''
        if self.date_order and self.sd_codigo_aduana and self.fcb_numero_dim_order:
            fecha = str(self.date_order.date())
            numero_dui = fecha[0:4] + self.sd_codigo_aduana[0:3] + self.fcb_numero_dim_order
        return numero_dui
