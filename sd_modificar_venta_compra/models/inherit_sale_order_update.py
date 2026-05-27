from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
from odoo.tools.misc import formatLang, get_lang
import pytz
class SdInheritSaleUpdate(models.Model):
	_inherit = "sale.order"

	def action_update_sale_order(self):
		pertenece_grupo = self.env['res.users'].has_group('sd_modificar_venta_compra.sd_update_sale_group')
		if pertenece_grupo:
			self.ensure_one()
			# self.validaciones_para_crear_factura_computarizada()
			action = self.env.ref(
				'sd_modificar_venta_compra.sd_action_wizard_sale_order_modificar').read()[0]
			return action
		else:
			raise UserError(
				_('No tiene Permiso para Modificar un Pedido de Venta'))
class SdInheritSaleOrderWidzar(models.TransientModel):
	_name = 'sd.sale.order.wizard'
	_check_company_auto = True

	@api.model
	def default_get(self, fields):
		res = super(SdInheritSaleOrderWidzar, self).default_get(fields)
		sale_order = self.env['sale.order']
		sale_id = self.env.context.get('default_move_id') or self.env.context.get('active_id')
		if sale_id:
			sale_order = self.env['sale.order'].browse(sale_id)
		if sale_order.exists():
			sale_order.ensure_one()
			if 'sale_id' in fields:
				res['sale_id'] = sale_order.id
			if 'partner_id' in fields:
				res['partner_id'] = sale_order.partner_id.id
			if 'date_order' in fields:
				res['date_order'] = sale_order.date_order
			if 'company_id' in fields:
				res['company_id'] = sale_order.company_id.id
			if 'currency_id' in fields:
				res['currency_id'] = sale_order.currency_id.id
			if 'work_process_order_id' in fields:
				res['work_process_order_id'] = sale_order.work_process_order_id.id
			if 'order_line' in fields:
				res['order_line'] = sale_order.order_line
			if 'user_id' in fields:
				res['user_id'] = sale_order.user_id.id
			if 'picking_policy' in fields:
				res['picking_policy'] = sale_order.picking_policy
			if 'warehouse_id' in fields:
				res['warehouse_id'] = sale_order.warehouse_id.id
			if 'require_signature' in fields:
				res['require_signature'] = sale_order.require_signature
			if 'team_id' in fields:
				res['team_id'] = sale_order.team_id.id
			if 'payment_term_id' in fields:
				res['payment_term_id'] = sale_order.payment_term_id.id
			if 'partner_shipping_id' in fields:
				res['partner_shipping_id'] = sale_order.partner_shipping_id.id
			if 'fiscal_position_id' in fields:
				res['fiscal_position_id'] = sale_order.fiscal_position_id.id
			if 'pricelist_id' in fields:
				res['pricelist_id'] = sale_order.pricelist_id.id
			if 'note' in fields:
				res['note'] = sale_order.note
			if 'name' in fields:
				res['name'] = sale_order.name
		return res
	def _get_default_require_signature(self):
		return self.env.company.portal_confirmation_sign
	@api.model
	def _default_warehouse_id(self):
		company = self.env.company.id
		warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
		return warehouse_ids

	@api.model
	def _get_invoice_default_compute_team(self):
		return self.env['crm.team']._get_default_team_id()

	@api.model
	def _default_note(self):
		return self.env['ir.config_parameter'].sudo().get_param(
			'account.use_invoice_terms') and self.env.company.invoice_terms or ''

	sale_id = fields.Many2one('sale.order', 'Venta', required=True, ondelete='cascade')
	partner_id = fields.Many2one('res.partner', store=True, check_company=True, string="Cliente",readonly=True)
	date_order = fields.Date(string="Fecha orden",check_company=True)
	company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company.id)
	currency_id = fields.Many2one('res.currency', 'Divisa', readonly=True)
	work_process_order_id = fields.Many2one('automated.sale', string='Tipo de Venta', readonly=True)
	order_wizard_line_ids = fields.One2many('sd.sale.order.wizard.line', 'sale_id')
	order_line = fields.One2many(related='sale_id.order_line', string='Lineas del Pedido')
	user_id = fields.Many2one('res.users', copy=False, tracking=True,string='Vendedor',default=lambda self: self.env.user)
	picking_policy = fields.Selection([
		('direct', 'Lo antes posible'),
		('one', 'Cuando todos los Productos esten listos')],
		string='Política de entrega', required=True, readonly=True, default='direct')
	warehouse_id = fields.Many2one('stock.warehouse', string='Almacén',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=_default_warehouse_id, check_company=True)
	require_signature = fields.Boolean('Firma en línea', default=_get_default_require_signature, readonly=True)

	team_id = fields.Many2one('crm.team', string='Equipo de Ventas', default=_get_invoice_default_compute_team,domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
	payment_term_id = fields.Many2one(
		'account.payment.term', string='Plazos de pago', check_company=True,  # Unrequired company
		domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
	partner_shipping_id = fields.Many2one(
		'res.partner', string='Dirección de entrega', readonly=True, required=True,
		states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
		domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
	fiscal_position_id = fields.Many2one(
		'account.fiscal.position', string='Fiscal Position',
		domain="[('company_id', '=', company_id)]", check_company=True,
		help="Fiscal positions are used to adapt taxes and accounts for particular customers or sales orders/invoices."
			 "The default value comes from the customer.")
	pricelist_id = fields.Many2one(
		'product.pricelist', string='lista precio', check_company=True,  # Unrequired company
		required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
		domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
		help="If you change the pricelist, only newly added lines will be affected.")
	note = fields.Text('Terminos y condiciones...', default=_default_note)
	name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
					   states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))

	@api.onchange('partner_id')
	def crear_sale_order_line_wizard(self):
		for line in self.order_line:
			values = ({
				'product_id': line.product_id.id,
				'name': line.name,
				'product_uom_qty': line.product_uom_qty,
				'product_uom': line.product_uom.id,
				'price_unit': line.price_unit,
				# 'tax_ids':tax_ids,
				'price_subtotal': line.price_subtotal,
				# 'partner_id': line.partner_id.id,
				# 'discount': line.discount,
				# 'company_id': line.company_id.id,
				'sale_id': self.id,
				'currency_id':line.currency_id.id
			})
			# self.env[self.computer_invoice_line_ids._name].new(values)
			self.env[self.order_wizard_line_ids._name].create(values)
	def confirmar_update_sale(self):
		#anular factura y conseguir su nombre
		name_invoice = self.anular_anterior_factura()
		name_picking = self.anular_anterior_picking()
		self.sale_id.write({'state': 'cancel'})
		sale_id = self.crear_sale_order()
		sale_id.action_confirm()
		print(sale_id.name,'name')
		self.crear_invoice_(name_invoice,sale_id)
	def crear_sale_order(self):
		objet_sale = self.env['sale.order']
		sale_id = objet_sale.create({
			'partner_id': self.partner_id.id,
			'pricelist_id': self.pricelist_id.id,
			'currency_id': self.currency_id.id,
			'name': self.name,
			'display_name': self.name,
			'user_id': self.user_id.id,
			'date_order': self.date_order,
			'picking_policy': self.picking_policy,
			'work_process_order_id': self.work_process_order_id.id,
			'warehouse_id': self.warehouse_id.id,
			'note': self.note,
			'team_id': self.team_id.id,
			'partner_shipping_id': self.partner_shipping_id.id,
			'fiscal_position_id': self.fiscal_position_id.id,
			'payment_term_id': self.payment_term_id.id,
			'require_signature': self.require_signature,
			'company_id': self.company_id.id,
		})
		self.crear_sale_order_line(sale_id)
		return sale_id
	def crear_sale_order_line(self,sale_id):
		order_line_obj = self.env['sale.order.line']
		for order_line in self.order_wizard_line_ids:
			order_line_obj.create({
				'order_id': sale_id.id,
				'product_id': order_line.product_id.id,
				'name': order_line.name,
				'product_uom_qty': order_line.product_uom_qty,
				'product_uom': order_line.product_uom.id,
				'price_unit': order_line.price_unit,
				'discount': order_line.discount,
				'product_uom_category_id': order_line.product_uom_category_id.id,
				'price_subtotal': order_line.price_subtotal,
				'tax_id': order_line.tax_id.id,
				'currency_id': order_line.currency_id.id,
				'company_id': order_line.company_id.id
			})
	def anular_anterior_factura(self):
		objeto_invoice = self.sale_id.invoice_ids
		objeto_invoice.sudo().button_draft()
		objeto_invoice.sudo().button_cancel()
		name_invoice = ''
		if objeto_invoice:
			name_invoice = objeto_invoice.name
			objeto_invoice.sudo().write({
				'name': 'Modificada' + ' ' + objeto_invoice.name,
				'display_name': 'Modificada' + ' ' + objeto_invoice.name,
			})
			if objeto_invoice.ref:
				objeto_invoice.sudo().write({
					'ref': 'Modificada ' + objeto_invoice.ref
				})
		return name_invoice
	def crear_invoice_(self,name,orden):
		user_tz = self.env.user.tz
		local = pytz.timezone(user_tz)
		date_order_factura = (pytz.utc.localize(orden.date_order).astimezone(local)).date()
		orden._create_invoices()
		invoice_new = orden.invoice_ids.filtered(lambda invoice: invoice.state != 'cancel')
		if orden.work_process_order_id.sales_journal:
			invoice_new.write({
				'journal_id': orden.work_process_order_id.sales_journal.id,
				'invoice_date': orden,
				'invoice_date_due': date_order_factura,
				'date': date_order_factura,
				'name': name,
				# 'display_name': name
			})
		invoice_new.post()


class SdInheritSaleOrderWidzarLine(models.TransientModel):
	_name = 'sd.sale.order.wizard.line'
	_check_company_auto = True
	sale_id = fields.Many2one('sd.sale.order.wizard', 'Orden de venta wizard',index=True, readonly=True, auto_join=True, ondelete="cascade")

	product_id = fields.Many2one('product.product', string='Producto', domain=[('purchase_ok', '=', True)],change_default=True)
	name = fields.Text(string='Descripción', required=True)
	product_uom_qty = fields.Float(string='Cantidad', digits='Product Unit of Measure', required=True, default=1.0)
	product_uom = fields.Many2one('uom.uom', string='Unit of Measure',domain="[('category_id', '=', product_uom_category_id)]")
	product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
	price_unit = fields.Float('Precio unidad', required=True, digits='Product Price', default=0.0)
	price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
	tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
	currency_id = fields.Many2one(related='sale_id.currency_id', depends=['sale_id.currency_id'], store=True, string='Currency', readonly=True)
	discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
	company_id = fields.Many2one(related='sale_id.company_id', string='Company', store=True, readonly=True, index=True)
	@api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
	def _compute_amount(self):
		"""
        Compute the amounts of the SO line.
        """
		for line in self:
			price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
			taxes = line.tax_id.compute_all(price, line.sale_id.currency_id, line.product_uom_qty,
											product=line.product_id, partner=line.sale_id.partner_shipping_id)
			line.update({
				# 'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
				# 'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})
			if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
					'account.group_account_manager'):
				line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

	@api.onchange('product_id')
	def product_id_change(self):
		if not self.product_id:
			return
		valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
		# # remove the is_custom values that don't belong to this template
		# for pacv in self.product_custom_attribute_value_ids:
		# 	if pacv.custom_product_template_attribute_value_id not in valid_values:
		# 		self.product_custom_attribute_value_ids -= pacv
		#
		# # remove the no_variant attributes that don't belong to this template
		# for ptav in self.product_no_variant_attribute_value_ids:
		# 	if ptav._origin not in valid_values:
		# 		self.product_no_variant_attribute_value_ids -= ptav

		vals = {}
		if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
			vals['product_uom'] = self.product_id.uom_id
			vals['product_uom_qty'] = self.product_uom_qty or 1.0

		product = self.product_id.with_context(
			lang=get_lang(self.env, self.sale_id.partner_id.lang).code,
			partner=self.sale_id.partner_id,
			quantity=vals.get('product_uom_qty') or self.product_uom_qty,
			date=self.sale_id.date_order,
			pricelist=self.sale_id.pricelist_id.id,
			uom=self.product_uom.id
		)

		vals.update(name=self.get_sale_order_line_multiline_description_sale(product))

		self._compute_tax_id()

		if self.sale_id.pricelist_id and self.sale_id.partner_id:
			vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
				self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
		self.update(vals)

		title = False
		message = False
		result = {}
		warning = {}
		if product.sale_line_warn != 'no-message':
			title = _("Warning for %s") % product.name
			message = product.sale_line_warn_msg
			warning['title'] = title
			warning['message'] = message
			result = {'warning': warning}
			if product.sale_line_warn == 'block':
				self.product_id = False

		return result

	def _compute_tax_id(self):
		for line in self:
			fpos = line.sale_id.fiscal_position_id or line.sale_id.partner_id.property_account_position_id
			# If company_id is set in the order, always filter taxes by the company
			taxes = line.product_id.taxes_id.filtered(lambda r: r.company_id == line.sale_id.company_id)
			line.tax_id = fpos.map_tax(taxes, line.product_id, line.sale_id.partner_shipping_id) if fpos else taxes

	def get_sale_order_line_multiline_description_sale(self, product):
		""" Compute a default multiline description for this sales order line.

        In most cases the product description is enough but sometimes we need to append information that only
        exists on the sale order line itself.
        e.g:
        - custom attributes and attributes that don't create variants, both introduced by the "product configurator"
        - in event_sale we need to know specifically the sales order line as well as the product to generate the name:
          the product is not sufficient because we also need to know the event_id and the event_ticket_id (both which belong to the sale order line).
        """
		return product.get_product_multiline_description_sale() #+ self._get_sale_order_line_multiline_description_variants()

	# def _get_sale_order_line_multiline_description_variants(self):
	# 	"""When using no_variant attributes or is_custom values, the product
    #     itself is not sufficient to create the description: we need to add
    #     information about those special attributes and values.
	#
    #     :return: the description related to special variant attributes/values
    #     :rtype: string
    #     """
	# 	if not self.product_custom_attribute_value_ids and not self.product_no_variant_attribute_value_ids:
	# 		return ""
	#
	# 	name = "\n"
	#
	# 	custom_ptavs = self.product_custom_attribute_value_ids.custom_product_template_attribute_value_id
	# 	no_variant_ptavs = self.product_no_variant_attribute_value_ids._origin
	#
	# 	# display the no_variant attributes, except those that are also
	# 	# displayed by a custom (avoid duplicate description)
	# 	for ptav in (no_variant_ptavs - custom_ptavs):
	# 		name += "\n" + ptav.with_context(lang=self.order_id.partner_id.lang).display_name
	#
	# 	# Sort the values according to _order settings, because it doesn't work for virtual records in onchange
	# 	custom_values = sorted(self.product_custom_attribute_value_ids,
	# 						   key=lambda r: (r.custom_product_template_attribute_value_id.id, r.id))
	# 	# display the is_custom values
	# 	for pacv in custom_values:
	# 		name += "\n" + pacv.with_context(lang=self.order_id.partner_id.lang).display_name
	#
	# 	return name
	def _get_display_price(self, product):
		# TO DO: move me in master/saas-16 on sale.order
		# awa: don't know if it's still the case since we need the "product_no_variant_attribute_value_ids" field now
		# to be able to compute the full price

		# it is possible that a no_variant attribute is still in a variant if
		# the type of the attribute has been changed after creation.
		# no_variant_attributes_price_extra = [
		# 	ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
		# 		lambda ptav:
		# 		ptav.price_extra and
		# 		ptav not in product.product_template_attribute_value_ids
		# 	)
		# ]
		# if no_variant_attributes_price_extra:
		# 	product = product.with_context(
		# 		no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra)
		# 	)

		if self.sale_id.pricelist_id.discount_policy == 'with_discount':
			return product.with_context(pricelist=self.sale_id.pricelist_id.id, uom=self.product_uom.id).price
		product_context = dict(self.env.context, partner_id=self.sale_id.partner_id.id, date=self.sale_id.date_order,
							   uom=self.product_uom.id)

		final_price, rule_id = self.sale_id.pricelist_id.with_context(product_context).get_product_price_rule(
			product or self.product_id, self.product_uom_qty or 1.0, self.sale_id.partner_id)
		base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
																						   self.product_uom_qty,
																						   self.product_uom,
																						   self.sale_id.pricelist_id.id)
		if currency != self.sale_id.pricelist_id.currency_id:
			base_price = currency._convert(
				base_price, self.sale_id.pricelist_id.currency_id,
				self.sale_id.company_id or self.env.company, self.sale_id.date_order or fields.Date.today())
		# negative discounts (= surcharge) are included in the display price
		return max(base_price, final_price)
