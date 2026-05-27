from odoo import api, fields, models, _
import time
from datetime import datetime, timedelta
import random
from pysiat.services.service_sincronizacion import ServiceSincronizacion
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import pysiat.functions as functions
from pysiat.services.service_operaciones import ServiceOperaciones
class TestFacturacionOnline(models.Model):
    _inherit = 'online.billing.siat'

    sd_tipo_venta_automate_id = fields.Many2one('automated.sale', string='Tipo de venta', copy=False)
    sd_products_ids = fields.One2many('product.template', 'sd_factura_online_id', string='Productos', copy=False,
                                      domain=[('sd_codigo_product_id', '!=', None)])
    sd_partner_id = fields.Many2one('res.partner', string='Cliente',copy=False,
                                    domain=[('vat', '!=', None)])

    sd_cufd_test_ids = fields.Many2many('factura.cufd','test_cufd_id',string='Cufds', copy=False,
                                        help='seleccionar cufd con vigencia menos a 24 horas.')

    sd_tipo_evento_id = fields.Many2one('mensaje.eventos.siat', string='Evento',copy=False)
    sd_evento_significativo_id = fields.Many2one('eventos.significativos.siat', string='Evento Significativo', copy=False)

    sd_numero_facturas = fields.Integer('Número de facturas', copy=False)
    sd_cafc_test = fields.Char('Cafc test', copy=False)
    # campos para test cufd
    sd_nro_cufd_test = fields.Integer('Cantidad de cufd', copy=False)
    sd_es_test = fields.Boolean(string='Test', copy=False, default=False)
    sd_fecha_test = fields.Datetime(string='Fecha anulacion', copy=False)
    sd_is_refund = fields.Boolean(string='Es Credito-Debito', copy=False, default=False)
    sd_codigo_documento_sector_test = fields.Selection(selection=lambda self: self.get_selection_field('tipo.documento.sector.siat'),
                                                  string='Test Documento sector')
    # sd_invoices_ids = fields.One2many(string='facturas', copy=False)
    sd_facturas_originales = fields.Many2many('account.move', 'sd_factura_online_id', string="Factura Originales",copy=False)
    def test_solicitud_cuis(self):
        i = 1
        self.solicitudCuis(test=True)
        # while i<=1:
        #     print('cuis',i,self.solicitudCuis(test=True))
        #     i += 1
        # print(self.verificar_comunicacion_siat())
        # automated = self.env['ir.cron'].search(
        #     [('model_id', '=', 'model_online_billing_siat')]).ir_actions_server_id.run()
        # cron_id = self.env['ir.model.data'].xmlid_to_res_id('sd_facturacion_en_linea_v13.sd_evento_significativo_cron')
        # automated = self.env['ir.cron'].search(
        #     [('id', '=', cron_id)]).ir_actions_server_id.run()
        # automated = self.env['ir.cron'].sudo().search([('id', '=', cron_id), ('active','=',False)])
        # print(automated.id)
        # active = not automated.active
        # automated.write({
        #     'active': active
        # })
        # print(automated)

    def test_sincronizacion_catalogos(self):
        i = 1
        while i <= 50:

            self.sincrotest(test=True)
            # if i % 2 == 0:
            #     time.sleep(2)
            print('test', i)
            if i == 25:
                time.sleep(2)

            i += 1

    def test_cud(self):
        i = 1
        while i <= 1:
            print('cufd', i, self.solicitudCufd(test=True))
            # time.sleep(20)
            i += 1

    def function_cada_diez_minutos(self, ids):
        facturas = self.env['online.billing.siat'].search([('id','in',ids)])
        for factura in facturas:
            factura.test_cud()
    def get_vals_c(self, partner_id):
        vals_c = {
            'company_id': self.company_id.id,
            'partner_id': partner_id.id,
            # 'partner_ref': self.partner_ref,
            'date_order': datetime.now(),
            'work_process_order_id': 1,
            # 'picking_type_id': self.picking_type_id.id,
            'user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'sd_origen_venta_id': self.id,
        }
        return vals_c

    def get_vals_c_lines(self, product_id, orders):
        vals_c_line = {
            'company_id': orders.company_id.id,
            'order_id': orders.id,
            'name': product_id.name,
            'product_uom_qty': random.choice(range(1,10)),
            'product_id': product_id.id,
            'price_unit': product_id.lst_price,
            'product_uom': product_id.uom_id.id,
            'tax_id': None
            # 'date_planned': orders_sale_2.date_order,
            # 'analytic_tag_ids': orders_2.analytic_tag_ids.ids,
        }
        return vals_c_line
    def get_vals_borrador_lines(self, product_id, factura):
        data = {
            'company_id': factura.company_id.id,
            'move_id': factura.id,
            'name': product_id.name,
            'product_id': product_id.id,
            'quantity': random.choice(range(1,10)),
            'product_uom_id': product_id.uom_id.id,
            'price_unit': product_id.lst_price,
            'account_id': 77,
        }
        return data
    # def test_factura_individual_borrador(self):
    #     partner_id = self.env['res.partner'].search([('name', '=', 'Franz Suarez')])
    #     product_ids_1 = self.env['product.product'].search([('type', '=', 'service')])
    #     i = 1
    #     while i <= 125:
    #         product_ids = random.choices(product_ids_1, k=random.choice(range(1, 5)))
    #         data = {
    #             'company_id': self.company_id.id,
    #             'partner_id': partner_id.id,
    #             'journal_id': self.sd_journal_id.id,
    #         }
    #         factura = self.env['account.move'].create(data)
    #         for product_id in product_ids:
    #             print('producto.de', product_id.name)
    #             vals = self.get_vals_borrador_lines(product_id, factura)
    #             self.env['account.move.line'].create(vals)
    #         print('numero factura', i)
    #         i += 1
    def test_factura_individual(self, nro=None):
        # partner_id = self.env['res.partner'].search([('name', '=', 'Franz Suarez')])
        # product_ids_1 = self.env['product.product'].search([('type', '=', 'service')])
        ventas_array = []
        i = 1
        hasta = nro or self.sd_numero_facturas or 125
        while i <= hasta:
            product_ids = random.choices(self.sd_products_ids, k=random.choice(range(1,5)))
            data = {
                'company_id': self.company_id.id,
                'partner_id': self.sd_partner_id.id,
                'work_process_order_id': self.sd_tipo_venta_automate_id.id,
                'pricelist_id': 1,
                'date_order': datetime.now(),
                'user_id': self.env.user.id,
            }
            # time.sleep(2)
            venta = self.env['sale.order'].create(data)
            ventas_array.append(venta)
            for product_id in product_ids:
                # print('producto test', product_id.name)
                vals = self.get_vals_c_lines(product_id, venta)
                self.env['sale.order.line'].create(vals)
            # factura = self.env['account.move'].search([('invoice_origin','=',venta.name)])
            # factura.write({
            #     'sd_es_test': True
            # })
            # print('ventas antes de automate',venta)
            venta.action_automate()
            factura = self.env['account.move'].search([('invoice_origin', '=', venta.name)])
            factura.write({
                'sd_es_test': True
            })
            print('numero de factura', str(i))
            i += 1
        return ventas_array

    def test_eventos_significativos(self):

        for cufd in self.sd_cufd_test_ids:
            es_facil ,fecha_fin, fecha_inicio = self.get_fecha_fin(cufd)

            if es_facil:
                for i in range(0,5):

                    data = {
                        'name': self.sd_tipo_evento_id.sd_descripcion +' '+ str(i),
                        'sd_factura_online_id': self.id,
                        'sd_fecha_ini': '19:00:09',
                        'sd_fecha_inicio': self.validar_campo(fecha_inicio,'Fecha inicio cufd del evento'),
                        'sd_fecha_fin': fecha_fin,
                        'sd_evento_id': self.validar_campo(self.sd_tipo_evento_id.id, 'Seleccione un evento y vuelva a intentar'),
                        'sd_cufd_id': cufd.id,
                        'sd_is_test': True
                    }
                    # print('datos', data)
                    evento_siat = self.env['eventos.significativos.siat'].create(data)
                    evento_siat.registroEvento(test=True)
            else:
                data = {
                    'name': self.sd_tipo_evento_id.sd_descripcion+' '+cufd.sd_fecha_string,
                    'sd_factura_online_id': self.id,
                    'sd_fecha_ini': '19:00:09',
                    'sd_fecha_inicio': fecha_inicio,
                    'sd_fecha_fin': fecha_fin,
                    'sd_evento_id': self.sd_tipo_evento_id.id,
                    'sd_cufd_id': cufd.id,
                    'sd_is_test': True
                }
                evento_siat = self.env['eventos.significativos.siat'].create(data)
                evento_siat.registroEvento(test=True)


    
    def validar_campo(self, campo, nombre):
        if not campo:
            raise UserError(_('El campo "%s" es necesario.') % (nombre))
        else:
            return campo
    
    def get_fecha_fin(self,cufd):
        if self.sd_tipo_evento_id.sd_codigo_clasificador in [5,6,7]:
            fecha_fin = cufd.sd_fecha_vigencia + timedelta(milliseconds=1)
            fecha_inicio = cufd.sd_fecha_vigencia - timedelta(milliseconds=1)
            es_facil = True
        else:
            # fecha_fin = datetime.now() - timedelta(hours=1)
            fecha_fin = cufd.sd_fecha_vigencia + timedelta(milliseconds=1)
            fecha_inicio = cufd.sd_fecha_vigencia - timedelta(milliseconds=1)
            es_facil = False
        return es_facil, fecha_fin, fecha_inicio
        


    def test_facturacion_paquetes(self):
        evento = self.sd_evento_significativo_id
        account_move = self.env['account.move']
        if evento:
            for i in range(0,10):
                product_id = random.choices(self.sd_products_ids)
                product_id = product_id[0]
                print('producto', product_id)
                facturas = []
                for i in range(self.sd_numero_facturas):
                    factura_vals = {
                        'type': 'out_invoice',  # tipo de factura, puede ser out_invoice o in_invoice
                        'partner_id': self.sd_partner_id,  # ID del cliente
                        'invoice_date': fields.Date.today(),  # fecha de la factura
                        'sd_fecha_emision': fields.Date.today(),
                        'journal_id': self.sd_journal_id.id,
                        'sd_es_test': True,
                        'invoice_line_ids': [
                            (0, 0, {
                                'product_id': product_id.id,  # nombre del producto
                                'quantity': 1.0,  # cantidad del producto
                                'price_unit': product_id.list_price,  # precio unitario del producto
                            })
                        ],
                    }
                    print('factura numero ', i + 1)
                    factura = account_move.create(factura_vals)
                    factura.post()
                    facturas.append(factura)
                # cant = self.sd_numero_facturas or random.choice(range(1, 5))
                # ventas = self.test_factura_individual(nro=cant)
                # array_facturas = []
                # for venta in ventas:
                #     # ('journal_id.fcb_es_electronico', '=', True), ('type', '=', 'out_invoice'), (
                #     # 'state', '=', 'draft'), ('journal_id', '=', self.sd_journal_id.id),
                #     factura = self.env['account.move'].search([('invoice_origin','=',venta.name)])
                #     # factura.cabecera.fechaEmision = functions.sb_siat_format_datetime(self.obtener_fecha_backend(evento.sd_fecha_inicio))
                #     array_facturas.append(factura)

                data = {
                    'name': 'paquete '+evento.name+' '+str(i+1),
                    'sd_factura_online_id': self.id,
                    'sd_evento_id': evento.id,
                    'sd_fecha_inicio': evento.sd_fecha_inicio,
                    'sd_codigo_sucursal': self.sd_codigo_sucursal,
                    'sd_tipo_factura': self.sd_tipo_factura,
                    'sd_codigo_documento_sector': self.sd_codigo_documento_sector,
                    'sd_invoice_ids': [factura.id for factura in facturas],
                    'sd_cafc': str(self.sd_cafc_test) if self.sd_cafc_test else None,
                }
                paquete_factura = self.env['siat.emision.paquete.offline'].create(data)
                paquete_factura.registroEmisionPaquetes(test=evento.sd_fecha_inicio)
                paquete_factura.validacionRecepcionPaquete(test=True)
                # print('Numero:',i)
        else:
            raise UserError(_('No existe un evento registrado con este tipo de evento'))
    def test_anulacion_factura(self):
        type = 'out_invoice' if not self.sd_is_refund else 'out_refund'
        facturas = self.env['account.move'].search([('journal_id.id', '=', self.sd_journal_id.id), ('type','=', type),
                                                    ('state', '=', 'posted'), ('sd_fecha_emision', '>', self.sd_fecha_test),
                                                    ('sd_codigo_documento_sector','=',self.sd_codigo_documento_sector_test), ('sd_es_test', '=', 'False')
                                                    ], limit=125, order='sd_fecha_emision desc')
        print('facturas a anular',facturas)
        i = 0
        for factura in self.sd_facturas_originales:
            factura.write({
                'sd_motivo_id': 1 if not self.sd_is_refund else 2
            })
            print(i+1)
            i += 1
            factura.button_cancel()

    # def test_nota_debito_credito(self):
    #     facturas = self.env['account.move'].search([('journal_id','=',self.sd_journal_id.id),
    #                                                 ('sd_fecha_emision', '>', '18/04/2023 17:29:26')], limit=125)
    #     print('Facturas',facturas)
    #     for factura in facturas:
    #         factura_rectificada = factura.action_reverse()
    #
    #         fact_rectifi = self.env['account.move'].search([('type','=','out_refund'), ('id','=',factura_rectificada['id'])])
    #         print(fact_rectifi)
    #         fact_rectifi.action_post()

    def test_factura_rectificadas(self):
        facturas_originales = self.sd_facturas_originales
        for factura in facturas_originales:
            factura_original = self.env['account.move'].search([('id', '=', factura.id)])
            if factura_original:
                # Crear un diccionario con los valores para la factura rectificativa
                refund_vals = {
                    'reason': 'Factura rectificativa',
                    'date': fields.Date.today(),
                    'refund_method': 'refund',
                    'move_id': factura_original.id,
                }

                # Crear la factura rectificativa
                reversal = self.env['account.move.reversal'].create(refund_vals)
                refund = reversal.reverse_moves()

                factura_refund = self.env['account.move'].search([('id', '=', refund['res_id']), ('type','=','out_refund')])
                factura_refund.write({'sd_factura_original': factura_original.id})
                print('rectificativa: ',factura_refund.sd_factura_original)
                # Guardar la factura rectificativa
                factura_refund.action_post()
        self.write({'sd_facturas_originales': []})
        return True

    def test_factura_masiva(self):
        account_move = self.env['account.move']
        for numero_masiva in range(10):
            product_id = random.choices(self.sd_products_ids)
            product_id = product_id[0]
            print('producto', product_id)
            facturas = []
            for i in range(self.sd_numero_facturas):
                factura_vals = {
                    'type': 'out_invoice',  # tipo de factura, puede ser out_invoice o in_invoice
                    'partner_id': 278,  # ID del cliente
                    'invoice_date': fields.Date.today(),  # fecha de la factura
                    'sd_fecha_emision': fields.Date.today(),
                    'journal_id': self.sd_journal_id.id,
                    'invoice_line_ids': [
                        (0, 0, {
                            'product_id': product_id.id,  # nombre del producto
                            'quantity': 1.0,  # cantidad del producto
                            'price_unit': product_id.list_price,  # precio unitario del producto
                        })
                    ],
                }
                print('factura numero ', i+1)
                factura = account_move.create(factura_vals)
                facturas.append(factura)
            data = {
                    'name': 'emision masiva ' + self.sd_journal_id.name + ' ' + str(numero_masiva + 1),
                    'sd_factura_online_id': self.id,
                    'sd_invoice_ids': [factura.id for factura in facturas],
                }
            masiva = self.env['siat.emision.masiva'].create(data)
            masiva.registroEmisionMasiva()
            masiva.validacionRecepcionMasiva()
            print('emision masiva numero ', numero_masiva+1)



