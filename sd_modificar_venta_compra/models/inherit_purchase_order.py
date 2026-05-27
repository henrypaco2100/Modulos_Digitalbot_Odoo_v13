from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang, get_lang
from dateutil.relativedelta import relativedelta
# import datetime
class SdInheritPurchaseUpdate(models.Model):
    _inherit = "purchase.order"
    def action_update_purchase_order(self):
        pertenece_grupo = self.env['res.users'].has_group('sd_modificar_venta_compra.sd_update_purchase_group')
        if pertenece_grupo:
            self.ensure_one()
            # self.validaciones_para_crear_factura_computarizada()
            action = self.env.ref('sd_modificar_venta_compra.sd_action_wizard_purchase_order_modificar').read()[0]
            return action
        else:
            raise UserError(_('No tiene Permiso para Modificar un Pedido de Compra'))

class SdInheritPurchaseOrderWidzar(models.TransientModel):
    _name = 'sd.purchase.order.wizard'
    _check_company_auto = True

    @api.model
    def default_get(self, fields):
        res = super(SdInheritPurchaseOrderWidzar, self).default_get(fields)
        purchase_order = self.env['purchase.order']
        purchase_id = self.env.context.get('default_move_id') or self.env.context.get('active_id')
        if purchase_id:
            purchase_order = self.env['purchase.order'].browse(purchase_id)
        if purchase_order.exists():
            purchase_order.ensure_one()
            if 'purchase_id' in fields:
                res['purchase_id'] = purchase_order.id
            if 'partner_id' in fields:
                res['partner_id'] = purchase_order.partner_id.id
            if 'date_order' in fields:
                res['date_order'] = purchase_order.date_approve
            if 'company_id' in fields:
                res['company_id'] = purchase_order.company_id.id
            if 'currency_id' in fields:
                res['currency_id'] = purchase_order.currency_id.id
            if 'work_process_order_id' in fields:
                res['work_process_order_id'] = purchase_order.work_process_order_id.id
            if 'order_line' in fields:
                res['order_line'] = purchase_order.order_line
            if 'user_id' in fields:
                res['user_id'] = purchase_order.user_id.id
            if 'picking_policy' in fields:
                res['picking_policy'] = purchase_order.picking_policy
            if 'picking_type_id' in fields:
                res['picking_type_id'] = purchase_order.picking_type_id.id
            if 'partner_ref' in fields:
                res['partner_ref'] = purchase_order.partner_ref
            if 'fiscal_position_id' in fields:
                res['fiscal_position_id'] = purchase_order.fiscal_position_id.id
            return res

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(self.env.context.get('company_id') or self.env.company.id)
        return warehouse_ids
    def _default_currency_id(self):
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.company.id
        return self.env['res.company'].browse(company_id).currency_id

    purchase_id = fields.Many2one('purchase.order', 'Compra', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', store=True, check_company=True, string="Cliente",readonly=True)
    date_order = fields.Date(string="Fecha confirmación", check_company=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', 'Divisa', readonly=True,default=_default_currency_id)
    work_process_order_id = fields.Many2one('automated.purchase', string='Tipo de Compra', readonly=True)
    order_wizard_line_ids = fields.One2many('sd.purchase.order.wizard.line', 'purchase_id')
    order_line = fields.One2many(related='purchase_id.order_line', string='Lineas del Pedido')
    user_id = fields.Many2one('res.users', copy=False, tracking=True, string='Vendedor',
                              default=lambda self: self.env.user)
    picking_policy = fields.Selection([
        ('direct', 'Lo antes posible'),
        ('one', 'Cuando todos los Productos esten listos')],
        string='Política de entrega', required=True, readonly=True, default='direct')
    picking_type_id = fields.Many2one('stock.picking.type', 'Entregar a',
                                      required=True, default=_default_picking_type,
                                      domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]")
    partner_ref = fields.Char('Referencia de proveedor', copy=False)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position',
                                         domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return picking_type[:1]
    @api.onchange('partner_id')
    def crear_purchase_order_line(self):
        for line in self.order_line:
            values = ({
                'product_id': line.product_id.id,
                'name': line.name,
                # 'account_id': line.account_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_qty':line.product_qty,
                'product_uom': line.product_uom.id,
                'price_unit': line.price_unit,
                # 'tax_ids':tax_ids,
                'price_subtotal': line.price_subtotal,
                'partner_id': line.partner_id.id,
                # 'discount': line.discount,
                'company_id': line.company_id.id,
                'purchase_id': self.id,
                'date_planned':line.date_planned,
                'currency_id':line.currency_id.id
            })
            # self.env[self.computer_invoice_line_ids._name].new(values)
            self.env[self.order_wizard_line_ids._name].create(values)
class SdInheritPurchaseOrderWidzarLine(models.TransientModel):
    _name = 'sd.purchase.order.wizard.line'
    _check_company_auto = True

    purchase_id = fields.Many2one('sd.purchase.order.wizard', 'Orden de Compra wizard',index=True, readonly=True, auto_join=True, ondelete="cascade")

    product_id = fields.Many2one('product.product', string='Producto', domain=[('purchase_ok', '=', True)],change_default=True)
    product_uom_qty = fields.Float(string='Cantidad', compute='_compute_product_uom_qty', store=True)
    name = fields.Text(string='Descripción', required=True)
    product_qty = fields.Float(string='Cantidad', digits='Product Unit of Measure', required=True)
    product_uom = fields.Many2one('uom.uom', string='Udm',domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    price_unit = fields.Float(string='Precio unidad', required=True, digits='Product Price')
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    taxes_id = fields.Many2many('account.tax', string='Taxes',domain=['|', ('active', '=', False), ('active', '=', True)])
    partner_id = fields.Many2one('res.partner', related='purchase_id.partner_id', string='Partner', readonly=True,store=True)
    currency_id = fields.Many2one(related='purchase_id.currency_id', store=True, string='Currency', readonly=True)
    company_id = fields.Many2one('res.company', related='purchase_id.company_id', string='Company', store=True,
                                 readonly=True)
    date_planned = fields.Datetime(string='Receipt Date', index=True)
    @api.depends('product_uom', 'product_qty', 'product_id.uom_id')
    def _compute_product_uom_qty(self):
        for line in self:
            if line.product_id and line.product_id.uom_id != line.product_uom:
                line.product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
            else:
                line.product_uom_qty = line.product_qty

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                # vals['partner']
            )
            line.update({
                # 'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                # 'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
    def _prepare_compute_all_values(self):
        # Hook method to returns the different argument values for the
        # compute_all method, due to the fact that discounts mechanism
        # is not implemented yet on the purchase orders.
        # This method should disappear as soon as this feature is
        # also introduced like in the sales module.
        self.ensure_one()
        return {
            'price_unit': self.price_unit,
            'currency_id': self.purchase_id.currency_id,
            'product_qty': self.product_qty,
            'product': self.product_id,
            # 'partner': self.purchase_id.partner_id,
        }

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return

        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.price_unit = self.product_qty = 0.0

        self._product_id_change()

        self._suggest_quantity()
        self._onchange_quantity()
    def _product_id_change(self):
        if not self.product_id:
            return

        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.company_id.id,
        )
        self.name = self._get_product_purchase_description(product_lang)

        self._compute_tax_id()
    def _suggest_quantity(self):
        '''
        Suggest a minimal quantity based on the seller
        '''
        if not self.product_id:
            return
        seller_min_qty = self.product_id.seller_ids\
            .filtered(lambda r: r.name == self.purchase_id.partner_id and (not r.product_id or r.product_id == self.product_id))\
            .sorted(key=lambda r: r.min_qty)
        if seller_min_qty:
            self.product_qty = seller_min_qty[0].min_qty or 1.0
            self.product_uom = seller_min_qty[0].product_uom
        else:
            self.product_qty = 1.0

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return
        params = {'purchase_id': self.purchase_id}
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.purchase_id.date_order,
            uom_id=self.product_uom,
            params=params)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            if self.product_id.seller_ids.filtered(lambda s: s.name.id == self.partner_id.id):
                self.price_unit = 0.0
            return

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                             self.product_id.supplier_taxes_id,
                                                                             self.taxes_id,
                                                                             self.company_id) if seller else 0.0
        if price_unit and seller and self.purchase_id.currency_id and seller.currency_id != self.purchase_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, self.purchase_id.currency_id, self.purchase_id.company_id, self.date_order or fields.Date.today())

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

        self.price_unit = price_unit
    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        return name
    def _compute_tax_id(self):
        for line in self:
            fpos = line.purchase_id.fiscal_position_id or line.purchase_id.partner_id.with_context(force_company=line.company_id.id).property_account_position_id
            # If company_id is set in the order, always filter taxes by the company
            taxes = line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id == line.purchase_id.company_id)
            line.taxes_id = fpos.map_tax(taxes, line.product_id, line.purchase_id.partner_id) if fpos else taxes

    @api.model
    def _get_date_planned(self, seller, po=False):
        """Return the datetime value to use as Schedule Date (``date_planned``) for
           PO Lines that correspond to the given product.seller_ids,
           when ordered at `date_order_str`.

           :param Model seller: used to fetch the delivery delay (if no seller
                                is provided, the delay is 0)
           :param Model po: purchase.order, necessary only if the PO line is
                            not yet attached to a PO.
           :rtype: datetime
           :return: desired Schedule Date for the PO line
        """
        date_order = po.date_order if po else self.purchase_id.date_order
        if date_order:
            return date_order + relativedelta(days=seller.delay if seller else 0)
        else:
            return datetime.today() + relativedelta(days=seller.delay if seller else 0)