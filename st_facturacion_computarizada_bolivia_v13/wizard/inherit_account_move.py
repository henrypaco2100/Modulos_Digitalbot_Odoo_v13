from collections import defaultdict

from odoo import api, fields, models, _
from collections import defaultdict
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero
from itertools import groupby

class AccountMoveCreateFactura(models.Model):
    _inherit = "account.move"

    def open_wizard_create_invoice_computer(self):
        pertenece_grupo = self.env['res.users'].has_group('st_facturacion_computarizada_bolivia_v13.group_invoice_move_computer_bolivia')
        if pertenece_grupo:
            self.ensure_one()
            self.validaciones_para_crear_factura_computarizada()
            action = self.env.ref('st_facturacion_computarizada_bolivia_v13.st_action_wizard_crear_factura_computarizada').read()[0]
            return action
        else:
            raise UserError(
                _('No tiene Permiso para Crear Factura Computarizada.'))
    def validaciones_para_crear_factura_computarizada(self):
        tax_ids = self.env['account.tax'].search([('type_tax_use', '=', 'sale')]).mapped('id')
        factura_computarizada = self.env['account.move'].search([('type', '=', 'out_invoice'),
                                                                 ('state', 'in', ['posted', 'draft']),
                                                                 ('invoice_origin', '=', self.invoice_origin),
                                                                 ('journal_id.fcb_es_computarizado', '=', True)])
        if not self.partner_id:
            raise UserError(
                _('Para Crear una Factura Computarizada es necesario el campo "Cliente".'))
        if not 'out_invoice' == self.type:
            raise UserError(
                _('Solo se permite Factura tipo Venta.'))
        if not 'posted' == self.state:
            raise UserError(
                _('Es necesario haber publicado la factura de Origen.'))
        if not tax_ids:
            raise UserError(
                _('No existe ningun Impuesto de tipo "Venta", porfavor Comuniquese con su Tecnico.'))
        if factura_computarizada.exists():
            raise UserError(
                _('Este documento cuenta con una factura Computarizada, no es posible continuar.'))


class FacturacionBoliviaWidzar(models.TransientModel):
    _name = 'account.move.wizard.computer'
    _check_company_auto = True

    @api.model
    def default_get(self, fields):
        res = super(FacturacionBoliviaWidzar, self).default_get(fields)
        account_move = self.env['account.move']
        move_id = self.env.context.get('default_move_id') or self.env.context.get('active_id')
        if move_id:
            account_move = self.env['account.move'].browse(move_id)
        if account_move.exists():
            account_move.ensure_one()
            if 'move_id' in fields:
                res['move_id'] = account_move.id
            if 'partner_id' in fields:
                res['partner_id'] = account_move.partner_id.id
            if 'invoice_date' in fields:
                res['invoice_date'] = account_move.invoice_date
            if 'currency_id' in fields:
                res['currency_id'] = account_move.currency_id.id
            if 'company_id' in fields:
                res['company_id'] = account_move.company_id.id
            if 'invoice_payment_term_id' in fields:
                res['invoice_payment_term_id'] = account_move.invoice_payment_term_id.id
            if 'invoice_date_due' in fields:
                res['invoice_date_due'] = account_move.invoice_date_due
            if 'ref' in fields:
                res['ref'] = account_move.ref
            if 'narration'in fields:
                res['narration'] = account_move.narration
            if 'invoice_partner_bank_id'in fields:
                res['invoice_partner_bank_id'] = account_move.invoice_partner_bank_id
            # if 'invoice_payment_ref'in fields:
            #     res['invoice_payment_ref'] = account_move.invoice_payment_ref
            if 'invoice_origin'in fields:
                res['invoice_origin'] = account_move.invoice_origin
            if 'transaction_ids' in fields:
                res['transaction_ids'] = [transaction for transaction in account_move.transaction_ids]

        return res

    move_id = fields.Many2one('account.move', 'factura', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', store=True, check_company=True, string="Cliente",readonly=True)
    invoice_date = fields.Date(string="Fecha Factura", readonly=True, check_company=True)
    company_id = fields.Many2one('res.company')
    currency_id = fields.Many2one('res.currency','Divisa', readonly=True)
    journal_id = fields.Many2one('account.journal','Diario', required=True, domain=[('fcb_es_computarizado', '=', True)])
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Plazo de pago')
    invoice_date_due = fields.Date(string='Plazo de pago', readonly=True, check_company=True)
    computer_invoice_line_ids = fields.One2many('account.move.computer.line','move_id')
    invoice_line_ids = fields.One2many(related='move_id.invoice_line_ids',string='lineas de fatura')
    invoice_user_id = fields.Many2one('res.users', copy=False, tracking=True,
        string='Vendedor',
        default=lambda self: self.env.user)
    invoice_origin = fields.Char(string='Documento Origen')
    narration = fields.Text(string='Terms and Conditions')

    @api.model
    def _get_invoice_default_compute_team(self):
        return self.env['crm.team']._get_default_team_id()

    team_id = fields.Many2one(
        'crm.team', string='Equipo de Ventas', default=_get_invoice_default_compute_team,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    ref = fields.Char(string='Reference', copy=False)
    invoice_partner_bank_id = fields.Many2one('res.partner.bank', string='Bank Account',
                                              help='Bank Account Number to which the invoice will be paid. A Company bank account if this is a Customer Invoice or Vendor Credit Note, otherwise a Partner bank account number.',
                                              domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    invoice_payment_ref = fields.Char(string='Payment Reference', index=True, copy=False,
                                      help="The payment reference to set on journal items.")
    transaction_ids = fields.Many2many('payment.transaction',string='Transacciones')
    # adicionales
    fcb_nit_a_facturar = fields.Char(string='Nit')
    fcb_nombre_a_facturar = fields.Char(string='Nombre a Facturar')

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        # ensure a correct context for the _get_default_journal method and company-dependent fields
        self = self.with_context(default_company_id=self.company_id.id, force_company=self.company_id.id)
        print('nita facturar',self.fcb_nit_a_facturar)
        invoice_vals = {
            'fcb_nit_a_facturar': self.fcb_nit_a_facturar,
            'fcb_nombre_a_facturar':self.fcb_nombre_a_facturar,
            'ref': self.ref or '',
            'type': 'out_invoice',
            'narration': self.narration,
            'currency_id': self.currency_id.id,
            # IMPLEMENTAR MAS ADELANTE
            'campaign_id': '',
            'medium_id': '',
            'source_id': '',
            'invoice_date':self.invoice_date,
            'invoice_user_id': self.invoice_user_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'invoice_partner_bank_id': self.invoice_partner_bank_id.id or self.company_id.partner_id.bank_ids[:1].id,
            'fiscal_position_id': self.partner_id.property_account_position_id.id,
            'journal_id': self.journal_id.id,
            'invoice_origin': self.invoice_origin,
            'invoice_payment_term_id': self.invoice_payment_term_id.id,
            'invoice_payment_ref': self.invoice_payment_ref,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'invoice_incoterm_id': '',
        }
        return invoice_vals

    @api.onchange('partner_id')
    def crear_computer_line(self):
        for line in self.invoice_line_ids:
            values = ({
                'product_id':line.product_id.id,
                'name':line.name ,
                'account_id':line.account_id.id,
                'quantity':line.quantity,
                'product_uom_id':line.product_uom_id.id,
                'price_unit':line.price_unit,
                # 'tax_ids':tax_ids,
                'price_subtotal':line.price_subtotal,
                'partner_id':line.partner_id.id,
                'discount':line.discount,
                'company_id':line.company_id.id,
                'move_id':self.id,
                'display_type':line.display_type,
                'analytic_account_id': line.analytic_account_id.id,
                'analytic_tag_ids': [analytic_tag_id.id for analytic_tag_id in line.analytic_tag_ids],
                })
            # self.env[self.computer_invoice_line_ids._name].new(values)
            self.env[self.computer_invoice_line_ids._name].create(values)

    def _create_invoices(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:
            pending_section = None

            # Invoice values.
            invoice_vals = order._prepare_invoice()

            # Invoice line values (keep only necessary sections).
            for line in order.computer_invoice_line_ids:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.quantity, precision_digits=precision):
                    continue
                if line.quantity > 0 or (line.quantity < 0 and final):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                        pending_section = None
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(
                    _('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            for grouping_keys, invoices in groupby(invoice_vals_list,
                                                   key=lambda x: [x.get(grouping_key) for grouping_key in
                                                                  invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    print('invoice',invoice_vals)
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['invoice_payment_ref'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        print('nombre',invoice_vals_list)
        moves = self.env['account.move'].with_context(default_type='out_invoice').create(invoice_vals_list)
        print('a facturar', moves.fcb_nit_a_facturar, moves.fcb_nombre_a_facturar)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        # for move in moves:
        #     move.message_post_with_view('mail.message_origin_link',
        #                                 values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
        #                                 subtype_id=self.env.ref('mail.mt_note').id
        #                                 )
        return moves
    def action_view_invoice(self, move):
        invoices = move.id
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(move) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(move) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_invoice',
        }

        action['context'] = context
        return action
    def create_invoices(self):
        self.validar_existe_tax_ids()
        move = self._create_invoices()
        move.action_post()
        action =self.action_view_invoice(move)

        return action
    def validar_existe_tax_ids(self):
        for line in self.computer_invoice_line_ids:
            if not line.tax_ids.exists():
                raise UserError(
                    _('Especifique el Impuesto en todas las lineas de la Factura.'))
    def _get_invoice_grouping_keys(self):
        return ['company_id', 'partner_id', 'currency_id']
    @api.onchange('fcb_nit_a_facturar')
    def maximo_caracteres(self):

        caracteres = self.fcb_nit_a_facturar
        diccionario_numerico = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
        if caracteres:
            for i in caracteres:
                if not i in diccionario_numerico:
                    self.fcb_nit_a_facturar = ''
                    return {
                        'warning': {
                            'message': _(
                                f'Se permiten solo caracteres numérico en el campo: "NIt", porfavor vuelva a intentarlo!!. ')
                        }
                    }

class AccountMoveComputerLine(models.TransientModel):
    _name = 'account.move.computer.line'
    _check_company_auto = True

    move_id = fields.Many2one('account.move.wizard.computer', 'Componente del factura del wizard',
                                      index=True,  readonly=True, auto_join=True, ondelete="cascade")
    name = fields.Char(string='Descripcion')
    company_id = fields.Many2one(related='move_id.company_id', store=True, readonly=True)
    account_id = fields.Many2one('account.account', string='Cuenta',
                                 index=True, ondelete="restrict", check_company=True,
                                 domain=[('deprecated', '=', False)])
    tax_ids = fields.Many2many('account.tax', string='Impuesto', domain=[('type_tax_use','=','sale')], required=True)
    price_unit = fields.Float(string='Precio', digits='Precio')
    product_uom_id = fields.Many2one('uom.uom', string='UDM')
    product_id = fields.Many2one('product.product', string='Producto')
    quantity = fields.Float(string='Cantidad',default=1.0, )
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,
                                     currency_field='always_set_currency_id')
    balance = fields.Monetary(string='Balance', store=True,
                              currency_field='company_currency_id',
                              compute='_compute_balance')
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
                                          readonly=True, store=True,)
    currency_id = fields.Many2one('res.currency', string='Currency')
    discount = fields.Float(string='Descuento (%)', digits='Discount', default=0.0)
    debit = fields.Monetary(string='Debit', default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(string='Credit', default=0.0, currency_field='company_currency_id')
    amount_currency = fields.Monetary(string='Monto en Moneda', store=True, copy=True)
    always_set_currency_id = fields.Many2one('res.currency', string='Foreign Currency',
                                             compute='_compute_always_set_currency_id')
    partner_id = fields.Many2one('res.partner', string='Cliente', ondelete='restrict')
    price_total = fields.Monetary(string='Total', store=True, readonly=True,
                                  currency_field='always_set_currency_id')
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note'),
    ], default=False, help="Technical field for UX purpose.")

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')


    @api.depends('currency_id')
    def _compute_always_set_currency_id(self):
        for line in self:
            line.always_set_currency_id = line.currency_id or line.company_currency_id


    @api.onchange('quantity', 'discount', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal(self):
        for line in self:

            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_fields_onchange_subtotal())
    def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, product=None, partner=None, taxes=None, move_type=None):
        self.ensure_one()
        return self._get_price_total_and_subtotal_model(
            price_unit=price_unit or self.price_unit,
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            currency=currency or self.currency_id,
            product=product or self.product_id,
            partner=partner or self.partner_id,
            taxes=taxes or self.tax_ids,
            move_type='out_refund',
        )

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * price_unit_wo_discount

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.compute_all(price_unit_wo_discount,
                                                  quantity=quantity, currency=currency, product=product,
                                                  partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, balance,  currency, taxes,
                                           price_subtotal, force_computation=False):
        ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance'.

        This method is a bit complex as we need to handle some special cases.
        For example, setting a positive balance with a 100% discount.

        :param quantity:        The current quantity.
        :param discount:        The current discount.
        :param balance:         The new balance.
        :param move_type:       The type of the move.
        :param currency:        The currency.
        :param taxes:           The applied taxes.
        :param price_subtotal:  The price_subtotal.
        :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
        '''

        sign = -1

        balance *= sign

        # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
        # issue.
        if not force_computation and currency.is_zero(balance - price_subtotal):
            return {}

        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):
            # Inverse taxes. E.g:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 110           | 10% incl, 5%  |                   | 100               | 115
            # 10            |               | 10% incl          | 10                | 10
            # 5             |               | 5%                | 5                 | 5
            #
            # When setting the balance to -200, the expected result is:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 220           | 10% incl, 5%  |                   | 200               | 230
            # 20            |               | 10% incl          | 20                | 20
            # 10            |               | 5%                | 10                | 10
            taxes_res = taxes._origin.compute_all(balance, currency=currency, handle_price_include=False)
            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.price_include:
                    balance += tax_res['amount']

        discount_factor = 1 - (discount / 100.0)
        if balance and discount_factor:
            # discount != 100%
            vals = {
                'quantity': quantity or 1.0,
                'price_unit': balance / discount_factor / (quantity or 1.0),
            }
        elif balance and not discount_factor:
            # discount == 100%
            vals = {
                'quantity': quantity or 1.0,
                'discount': 0.0,
                'price_unit': balance / (quantity or 1.0),
            }
        elif not discount_factor:
            # balance of line is 0, but discount  == 100% so we display the normal unit_price
            vals = {}
        else:
            # balance is 0, so unit price is 0 as well
            vals = {'price_unit': 0.0}
        return vals

    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for line in self:
            line.balance = line.debit - line.credit

    def _get_fields_onchange_subtotal(self, price_subtotal=None, currency=None, company=None, date=None):
        self.ensure_one()
        return self._get_fields_onchange_subtotal_model(
            price_subtotal=price_subtotal or self.price_subtotal,
            currency=currency or self.currency_id,
            company=company or self.move_id.company_id,
            date=date or self.move_id.invoice_date,
        )
    @api.model
    def _get_fields_onchange_subtotal_model(self, price_subtotal, currency, company, date):
        ''' This method is used to recompute the values of 'amount_currency', 'debit', 'credit' due to a change made
        in some business fields (affecting the 'price_subtotal' field).

        :param price_subtotal:  The untaxed amount.
        :param move_type:       The type of the move.
        :param currency:        The line's currency.
        :param company:         The move's company.
        :param date:            The move's date.
        :return:                A dictionary containing 'debit', 'credit', 'amount_currency'.
        '''

        sign = -1

        price_subtotal *= sign

        if currency and currency != company.currency_id:
            # Multi-currencies.
            balance = currency._convert(price_subtotal, company.currency_id, company, date)
            return {
                'amount_currency': price_subtotal,
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            }
        else:
            # Single-currency.
            return {
                'amount_currency': 0.0,
                'debit': price_subtotal > 0.0 and price_subtotal or 0.0,
                'credit': price_subtotal < 0.0 and -price_subtotal or 0.0,
            }
    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': '',
            # 'move_id': move.id,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'quantity': self.quantity,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_ids.ids)],
            'analytic_account_id': self.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            # 'sale_line_ids': [(4, self.id)],
        }
        if self.display_type:
            res['account_id'] = False
        return res


