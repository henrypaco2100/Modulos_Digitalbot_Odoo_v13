# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _, tools
from odoo.exceptions import Warning, UserError
from datetime import date,datetime
from odoo.exceptions import UserError, ValidationError
import datetime

class AutomatedSaleOrder(models.Model):
	_name = "automated.sale"
	_description = "Automated Sale"
	_order = 'sequence'

	name = fields.Char(string="Nombre")
	sequence = fields.Integer(string="Secuencia", default=10)
	payment_journal = fields.Many2one("account.journal", string ="Diario de Pago",domain=[['type', 'in',['bank','cash']]])
	company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.company)
	sales_journal = fields.Many2one("account.journal",string="Diario de Ventas",
	domain="[('type', 'in',['sale']), ('company_id', '=', company_id)]")
	work_order_process_id_p2 = fields.Many2one('automated.sale', string="Flujo de Venta Empresa 2")
	i_impuestos_flujo2 = fields.Many2many('account.tax', string="Impuestos",
										  domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'sale')]",)
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
							if len(cadena_secuencia) >= 10:
								if cadena_secuencia == 'sale.order':
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
		bandera_primer_punto = False
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
								if cadena_secuencia == 'sale.quotation':
									nuevo_objeto_secuencia.append(secuencia.id)
									break
								else:
									break
						else:
							if letra == '.':
								bandera_primer_punto = True
		return nuevo_objeto_secuencia

	st_almacen = fields.Many2one('stock.warehouse', string="almacén")
	st_secuencia = fields.Many2one('ir.sequence', string="Secuencia venta")#domain= lambda self:[('id', 'in', self._filtrar_secuencia())]
	st_secuencia_quotation = fields.Many2one('ir.sequence', string="Secuencia Cotizacion")#domain=lambda self: [('id', 'in', self._filtrar_secuencia_quotation())]

	validation_order = fields.Boolean("Validar orden")
	validation_picking = fields.Boolean("Validar Entrega")
	force_transfer = fields.Boolean("Forzar trasferencia, incluso si no esta disponible.")
	create_incoice = fields.Boolean("Crear Factura")
	validate_invoice = fields.Boolean("Validar Factura")
	register_payment = fields.Boolean("Registrar Pago")
	# force_invoice = fields.Boolean("Forzar Fecha de Factura")

	shipping_policy =fields.Selection([
		('direct', 'Entregue cada producto cuando esté disponible'),
		('one', 'Entregue todos los productos a la vez')],
		string='Politica de envios',required=True)
	invoicing_policy =  fields.Selection(
		[('order', 'Cantidades pedidas'),
		 ('delivery', 'Cantidades entregadas'),
		], string='Política de facturación',required=True)
	sd_is_numero_recibo = fields.Boolean(string='Nro Recibo',default=False)
	sd_is_numero_factura = fields.Boolean(string='Nro Factura',default=False)
	sd_is_ref = fields.Boolean(string='Nota de Entrega', default=False)
	# CAMPO PARA LAS RESTRINCIONES POR USUARIOS
	user_ids = fields.Many2many(
		'res.users',
		'res_automate_sale_users_rel',
		'cid', 'user_id',
		'Usuario'
	)

	@api.onchange('validate_invoice','register_payment')
	def depends_force(self):
		# if self.force_invoice == True:
		# 	self.validate_invoice = True

		if self.validate_invoice == True:
			self.create_incoice = True

		if self.register_payment == True:
			self.validate_invoice = True
			
	
	@api.onchange('force_transfer','validation_picking')
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

class InheritPartner(models.Model):
	_inherit = "res.partner"

	is_automated = fields.Boolean(string="Flujo de Trabajo Automatizado",default="True")
	work_process_id = fields.Many2one("automated.sale",string="Tipo de Venta")

class InheritSale(models.Model):
	_inherit = "sale.order"

	sd_origen_venta_id = fields.Many2one('sale.order', string="Venta origen")
	sd_venta_contable = fields.Many2one('sale.order', string="Venta Otra compañia")
	is_related = fields.Boolean(related="partner_id.is_automated")
	work_process_order_id = fields.Many2one("automated.sale",string="Tipo de Venta",domain=lambda self: [('id', 'in', self.env.user.automated_sale_ids.ids)])
	st_orden_cancelada = fields.Boolean(default=False)
	# Campo adiccion recibo factura
	sd_numero_recibo = fields.Char(string='Nro Recibo')
	sd_numero_factura = fields.Char(string='Nro Factura')
	sd_is_nro_recibo = fields.Boolean(related='work_process_order_id.sd_is_numero_recibo')
	sd_is_nro_factura = fields.Boolean(related='work_process_order_id.sd_is_numero_factura')
	# campo referencia entrega
	sd_ref_entrega = fields.Char(string='Nota de Entrega')
	sd_is_ref = fields.Boolean(related='work_process_order_id.sd_is_ref')
	sd_register_payment = fields.Boolean("Registrar Pago", related='work_process_order_id.register_payment')
	sd_glosa_payment = fields.Char('Glosa del Pago')
	#Metodos Adicionados
	@api.onchange('work_process_order_id')
	def _controlar_flujo_de_trabajo(self):
		if self.work_process_order_id:
			self.warehouse_id = self.work_process_order_id.st_almacen


	@api.onchange('warehouse_id')
	def _controlar_almacen(self):
		if self.warehouse_id:
			if self.work_process_order_id:
				if not self.warehouse_id.id == self.work_process_order_id.st_almacen.id:
					return {
						'warning': {
							'message': _(
								'El campo Flujo de Trabajo y Almacen son de distintos .')
						}
					}


	# Heredamos el metodo action_confirmar para editar la fecha de venta

	def action_confirm(self):

		if self._get_forbidden_state_confirm() & set(self.mapped('state')):
			raise UserError(_(
				'It is not allowed to confirm an order in the following states: %s'
			) % (', '.join(self._get_forbidden_state_confirm())))

		for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
			order.message_subscribe([order.partner_id.id])
		#se modifica el action_confirmar para poder ingresar cualquier fecha y asi no sea automatica del dia presente
		date_order = self.date_order
		self.write({
			'state': 'sale',
			#'date_order':fields.Datetime.now(), COLOCAR EL NIT
			'date_order': date_order
		})

		# Context key 'default_name' is sometimes propagated up to here.
		# We don't need it and it creates issues in the creation of linked records.
		context = self._context.copy()
		context.pop('default_name', None)

		self.with_context(context)._action_confirm()
		if self.env.user.has_group('sale.group_auto_done_setting'):
			self.action_done()
		return True
	@api.onchange("partner_id")
	def change_workflow(self):
		self.work_process_order_id = self.partner_id.work_process_id

	def action_automate(self):
		if not self.sudo().verificar_invoices_picking():
			if self.work_process_order_id:

				date_order = self.date_order
				date_order_factura_pago = (date_order - datetime.timedelta(hours=4)).date()
				# Order Configuration
				self.picking_policy = self.work_process_order_id.shipping_policy
				for line in self.order_line:
					line.product_id.sudo().write({
						'invoice_policy':self.work_process_order_id.invoicing_policy
					})
					# parametros = []
					# parametros.append(self.work_process_order_id.invoicing_policy)
					# parametros.append(line.product_id.id)
					# self.env.cr.execute("UPDATE public.product_product SET invoice_policy=%s WHERE id=%s ", (parametros))

				# validar Orden y crear Entrega
				if self.work_process_order_id.validation_order == True:
					self.sudo().validate_order_and_create_picking(date_order,date_order_factura_pago)

				# crear factura, confirmar y crear pago si es necesario
				if self.work_process_order_id.create_incoice == True:
					self.sudo().create_and_confirm_invoice(date_order_factura_pago)
				#si tiene doble contabilidad
				if self.work_process_order_id.work_order_process_id_p2:
					self._duplicate_sale_order_multicompany()
			else:
				raise Warning(('El campo Tipo de Venta es obligatorio.') )
		else:
			self.write({
				'state': 'sale'
			})

	def verificar_invoices_picking(self):
		existen_elementos = False
		if len(self.invoice_ids) > 0:
			existen_elementos = True
		elif len(self.picking_ids) > 0:
			existen_elementos = True
		return existen_elementos
	def validate_order_and_create_picking(self,date_order,date_order_factura_pago):
		""" este metodo se encarga de validar la orden y realizar el picking """

		picking_confirm = self.sudo().action_confirm()
		for order in self:
			if self.work_process_order_id.validation_picking == True or self.work_process_order_id.force_transfer == True:
				picking_ids = self.picking_ids
				for picking_id in self.picking_ids:
					for move_line in picking_id.move_lines:
						move_line.sudo().update({'quantity_done': move_line.product_uom_qty, })
					# Validar con el metodo automatico de Odoo-HENRY
					# object_picking_transfer_inmediate = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking_id.id)]})
					# object_picking_transfer_inmediate.sudo().process()
					picking_id.button_validate()
					# picking_id.action_done()

				# se sobreescribe o modifica la fecha efectiva en orden entrega
				picking_ids.write({'date_done': date_order})

				# escribir fecha en movimiento existencias, asientos contables, productos y valoracion de inventario
				objeto_stock_move = self.env['stock.move'].search([('picking_id', '=', picking_ids.id)])
				if objeto_stock_move:
					for stock_move in objeto_stock_move:
						stock_move.write({'date': date_order})
						objeto_account_move = self.env['account.move'].sudo().search([('stock_move_id', '=', stock_move.id)])
						if objeto_account_move:
							for account_move in objeto_account_move:
								account_move.sudo().write({'date': date_order_factura_pago})
						objeto_stock_valuation_layer = self.env['stock.valuation.layer'].search(
							[('stock_move_id', '=', stock_move.id)])
						if objeto_stock_valuation_layer:
							for stock_valuation_layer in objeto_stock_valuation_layer:
								parametros = []
								parametros.append(date_order)
								parametros.append(stock_valuation_layer.id)
								self.env.cr.execute(
									"UPDATE public.stock_valuation_layer SET create_date=%s WHERE id=%s ", (parametros))

				objeto_stock_move_line = self.env['stock.move.line'].search([('picking_id', '=', picking_ids.id)])
				if objeto_stock_move_line:
					for stock_move_line in objeto_stock_move_line:
						stock_move_line.write({'date': date_order})


	def create_and_confirm_invoice(self,date_order_factura_pago):
		"""Crear y confirmar factura,
		 tambien realizara el pago si es Necesario"""

		create_invoice = self.sudo()._create_invoices()
		invoice_obj = self.env['account.move'].sudo().search([('invoice_origin', '=', self.name), ('state', '!=', 'cancel')])

		if self.work_process_order_id.sales_journal:
			invoice_obj.sudo().write({
				'journal_id': self.work_process_order_id.sales_journal.id,
				'invoice_date': date_order_factura_pago,
				'invoice_date_due': date_order_factura_pago,
				'date': date_order_factura_pago,
			})
		# Numero de recibo
		if self.sd_is_nro_recibo:
			existe_recibo = True
			if self.work_process_order_id.validate_invoice:
				existe_recibo = True if self.sd_numero_recibo else False
			invoice_obj.sudo().write({
				'sd_numero_recibo': self.sd_numero_recibo,
				'sd_is_numero_recibo': existe_recibo,
			})
		# NUemro de factura
		if self.sd_is_nro_factura:
			existe_factura = True
			if self.work_process_order_id.validate_invoice:
				existe_factura = True if self.sd_numero_factura else False
			invoice_obj.sudo().write({
				'sd_numero_factura': self.sd_numero_factura,
				'sd_is_numero_factura': existe_factura,
			})
		# referencia Entrega
		if self.sd_is_ref:
			existe_factura = True
			if self.work_process_order_id.validate_invoice:
				existe_factura = True if self.sd_ref_entrega else False
			invoice_obj.sudo().write({
				'sd_ref_entrega_sale': self.sd_ref_entrega,
				'sd_is_ref_sale': existe_factura,
			})

		if self.work_process_order_id.register_payment == True and self.work_process_order_id.validate_invoice == True:
			self.create_payment(invoice_obj,date_order_factura_pago)
			# escribir fecha apuntes contables glosa apuntes contable
			objeto_move_line = self.env['account.move.line'].sudo().search([('move_id', '=', invoice_obj.id)])
			if objeto_move_line:
				for account_move_line in objeto_move_line.sudo().filtered(lambda l: l.exclude_from_invoice_tab == True):
					account_move_line.sudo().name = 'Factura del Cliente ' + invoice_obj.name + ', Venta: ' + self.name


		elif self.work_process_order_id.validate_invoice == True:  # or self.work_process_order_id.force_invoice==True
			validate = invoice_obj.sudo().action_post()

			# escribir fecha apuntes contables glosa apuntes contable
			objeto_move_line = self.env['account.move.line'].sudo().search([('move_id', '=', invoice_obj.id)])
			if objeto_move_line:
				for account_move_line in objeto_move_line.sudo().filtered(lambda l:	 l.exclude_from_invoice_tab == True):
					account_move_line.sudo().name ='Factura del Cliente ' + invoice_obj.name + ', Venta: ' + self.name

	def create_payment(self,invoice_obj,date_order_factura_pago):
		""" Este metodo se encarga de crear el pado de la factura"""

		validate = invoice_obj.action_post()
		payment = self.env['account.payment']
		payment_method = self.env['account.payment.method'].search([], limit=1)
		for inv in invoice_obj:
			res = payment.create({

				'partner_id': inv.partner_id.id,
				'amount': inv.amount_total,
				'payment_type': 'inbound',
				'partner_type': 'customer',
				'payment_method_id': payment_method.id,
				'journal_id': self.work_process_order_id.payment_journal.id,
				'payment_date': date_order_factura_pago,
				'communication': inv.name + " " + self.sd_glosa_payment if self.sd_glosa_payment else ' ',
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
	def _duplicate_sale_order_multicompany(self):
		# todo David en la linea 184 se comenta porque al momento de querer validar la venta
		# no se puede registrar ya que el picking type pertenece a una compañia en especifico
		vals_c = self.get_vals_c()
		orders_sale_2 = self.env['sale.order'].sudo().create(vals_c)

		line_ids = []
		for lines in self.order_line:
			vals_c_line = self.get_vals_c_lines(lines, orders_sale_2)
			line_ids.append(vals_c_line)
			imp = (self.work_process_order_id.work_order_process_id_p2.i_impuestos_flujo2).filtered(
				lambda x: x.company_id.id == self.work_process_order_id.work_order_process_id_p2.company_id.id)
		if vals_c_line['tax_id'].id == imp.id:
			for line_id in line_ids:
				orders_sale_2.order_line.sudo().create(line_id)
			orders_sale_2.action_automate()
		else:
			raise UserError(_("Error en los impuestos establecidos elija impuestos validos."))
		orders_sale_2.sd_origen_venta_id.update({
			"sd_venta_contable": orders_sale_2.id
		})
	'''
	Esta función obtiene los valores que se necesitan para crear la venta doble
	Esta puede realizarse sin datos de entrada  .. by Franz 
	'''

	def get_vals_c(self):
		vals_c = {
			'company_id': self.work_process_order_id.work_order_process_id_p2.company_id.id,
			'partner_id': self.partner_id.id,
			# 'partner_ref': self.partner_ref,
			'date_order': self.date_order,
			'work_process_order_id': self.work_process_order_id.work_order_process_id_p2.id,
			# 'picking_type_id': self.picking_type_id.id,
			'user_id': self.user_id.id,
			'team_id': self.team_id.id,
			'sd_origen_venta_id': self.id,
		}
		return vals_c

	'''
	   Esta función obtiene los valores para crear las lineas de venta de detalle.
	   solo necesita pasarles las lineas de las ordenes y la orden en general ... by Franz
	'''

	def get_vals_c_lines(self, lines, orders):
		vals_c_line = {
			'company_id': orders.company_id.id,
			'order_id': orders.id,
			'name': lines.name,
			'product_uom_qty': lines.product_uom_qty,
			'product_id': lines.product_id.id,
			'price_unit': lines.price_unit,
			'product_uom': lines.product_uom.id,
			'tax_id': self.sudo().work_process_order_id.work_order_process_id_p2.i_impuestos_flujo2.filtered(
				lambda x: x.company_id.id == self.work_process_order_id.work_order_process_id_p2.company_id.id)
			# 'date_planned': orders_sale_2.date_order,
			# 'analytic_tag_ids': orders_2.analytic_tag_ids.ids,
		}
		return vals_c_line
	# Arreglar el duplicate y pasarle la fecha-Henry 2022
	def copy(self, vals = None):
		if self.date_order:
			vals ={'date_order': self.date_order}
			res = super(InheritSale, self).copy(vals)
		else:
			res = super(InheritSale, self).copy()
		return res
	# restringir automated por usuario
	@api.model
	def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
		user = self.env.user
		# print('user', self.env.user.name)
		# if superadmin, do not apply
		if not self.env.is_superuser():
			args += ['|', ('work_process_order_id', '=', False), ('work_process_order_id', 'in', user.automated_sale_ids.ids)]
		return super()._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)

	@api.model
	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
		user = self.env.user
		# print('user', self.env.user.name)
		if not self.env.is_superuser():
			# Filtrar los registros por los IDs permitidos para el usuario actual
			allowed_automated_sale_ids = user.automated_sale_ids.ids
			domain += [('work_process_order_id', 'in', allowed_automated_sale_ids)]
		res = super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
		return res

# class SdSaleReport(models.Model):
# 	_inherit = 'sale.report'
# 	work_process_order_id = fields.Many2one(
# 			'automated.sale',
# 			string='Tipo de venta',
# 			readonly=True
# 		)
# 	def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
# 		fields = fields.copy()
# 		fields['work_process_order_id'] = ", s.work_process_order_id as work_process_order_id"
# 		groupby += ", s.work_process_order_id"
# 		return super()._query(with_clause, fields, groupby, from_clause)
#
# 	def init(self):
# 		tools.drop_view_if_exists(self.env.cr, self._table)
# 		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
# 	@api.model
# 	def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
# 		user = self.env.user
# 		# print('user', self.env.user.name)
# 		# if superadmin, do not apply
# 		if not self.env.is_superuser():
# 			args += ['|', ('work_process_order_id', '=', False),
# 					 ('work_process_order_id', 'in', user.automated_sale_ids.ids)]
# 		return super()._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)
#
# 	@api.model
# 	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
# 		user = self.env.user
# 		# print('user', self.env.user.name)
# 		if not self.env.is_superuser():
# 			# Filtrar los registros por los IDs permitidos para el usuario actual
# 			allowed_automated_sale_ids = user.automated_sale_ids.ids
# 			domain += [('work_process_order_id', 'in', allowed_automated_sale_ids)]
# 		res = super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
# 		return res