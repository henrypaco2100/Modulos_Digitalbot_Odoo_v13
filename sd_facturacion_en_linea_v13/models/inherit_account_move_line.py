from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round as round, float_compare

from odoo.odoo.exceptions import UserError


class SDAccountMoveLineDescuentoLinea(models.Model):
    _inherit = 'account.move.line'

    sd_descuento_adicional_linea = fields.Float(string='DAL', default=0.0)
    # sd_monto_gift_card = fields.Float(string='Monto giftCard')

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
        # CODIGO ADICIONAL AL METODO ORIGINAL, CALCULA EL DESCUENTO QUE CORRESPONDE
        # A LA LINEA Y LO RESTA AL TOTAL
        descuento_add = 0
        es_admin = self.env['res.users'].has_group(
            'sd_facturacion_en_linea_v13.sd_facturacion_electronica_en_linea_group')
        if ((self.move_id.sd_descuento_adicional and es_admin) or self.move_id.sd_cantidad_gift_card):
            print('es admin _get_price_total_and_subtotal_model')
            # Compute 'price_subtotal'.
            if not self.exclude_from_invoice_tab:
                descuento_add = self.monto_descuento_por_linea()
                price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
                subtotal = (quantity * price_unit_wo_discount) - descuento_add
            else:
                price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
                subtotal = (quantity * price_unit_wo_discount)
        #     FIN DEL CODIGO ADICIONAL, DENTRO DE LA CONDICION ELSE ESTA EL CODIGO ORIGINAL
        else:
            price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
            subtotal = (quantity * price_unit_wo_discount)

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1).compute_all(price_unit_wo_discount,
                                                                             quantity=quantity, currency=currency,
                                                                             product=product, partner=partner,
                                                                             is_refund=move_type in (
                                                                                 'out_refund', 'in_refund'),
                                                                             descuento_add=descuento_add)
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
            # print('taxes_res: ', taxes_res)
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, balance, move_type, currency, taxes,
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
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
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
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1

            # CODIGO ADICIONAL PARA CALCULAR DESCUENTO QUE CORRESPONDE A LA LINEA
            descuento = 0
            es_admin = self.env['res.users'].has_group(
                'sd_facturacion_en_linea_v13.sd_facturacion_electronica_en_linea_group')
            if (self.move_id.sd_descuento_adicional and es_admin) or self.move_id.sd_cantidad_gift_card:
                descuento = self.monto_descuento_por_linea()
                if self.exclude_from_invoice_tab:
                    descuento = 0
            # elif self.move_id.sd_cantidad_gift_card:
            #     descuento = self.monto_descuento_por_linea()
            #     if self.exclude_from_invoice_tab:
            #         descuento = 0

            # FIN DE CODIGO ADICIONAL

            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(balance, currency=currency,
                                                                                      handle_price_include=False,
                                                                                      descuento_add=descuento)
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


    def monto_descuento_por_linea(self):
        total = 0
        descuento = 0
        for line in self.move_id.invoice_line_ids:
            total += line.price_unit * line.quantity
        if self in self.move_id.invoice_line_ids:
            descuento = (((self.price_unit * self.quantity) * (self.move_id.sd_descuento_adicional + self.move_id.sd_cantidad_gift_card)) / total)
        # print('DESCUENTO: ', descuento)
        return descuento

    @api.onchange('quantity', 'price_unit', 'tax_ids')
    def recalcular_linea(self):
        self.sd_descuento_adicional_linea = self.monto_descuento_por_linea()
        self.price_total = (self.price_unit * self.quantity) - self.sd_descuento_adicional_linea
        # self._onchange_mark_recompute_taxes()
        self._onchange_price_subtotal()
        # self._get_price_total_and_subtotal_model(self.price_unit, self.quantity, self.discount, self.move_id.currency_id,
        #                                          self.product_id, self.move_id.partner_id, self.tax_ids, self.move_id.type)


class SDAccountMoveDescuentoAdicional(models.Model):
    _inherit = 'account.move'

    sd_descuento_adicional = fields.Float(string='Descuento Adicional', default=0.0)

    @api.onchange('sd_descuento_adicional', 'invoice_line_ids', 'sd_cantidad_gift_card')
    def _onchange_descuento_adicional(self):
        print('onchange 1')
        self._recompute_tax_lines(recompute_tax_base_amount=True)
        self._compute_invoice_taxes_by_group()
        for line in self.invoice_line_ids:
            line.recalcular_linea()


    @api.onchange('invoice_line_ids', 'sd_descuento_adicional', 'sd_cantidad_gift_card')
    def _onchange_invoice_line_ids(self):
        current_invoice_lines = self.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab)
        others_lines = self.line_ids - current_invoice_lines
        if others_lines and current_invoice_lines - self.invoice_line_ids:
            others_lines[0].recompute_tax_line = True
        self.line_ids = others_lines + self.invoice_line_ids
        self._recompute_dynamic_lines(recompute_all_taxes=True)

    def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):
        """ Compute the dynamic tax lines of the journal entry.

        :param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
        """
        self.ensure_one()

        # subtotal = 0
        # for line in self.invoice_line_ids:
        #     subtotal += line.quantity * line.price_unit
        # for line in self.invoice_line_ids:
        #     descuento_subtotal = (((line.price_unit * line.quantity) / subtotal) * self.sd_descuento_adicional) / line.quantity
        #     print('descuento a subtotal: ', descuento_subtotal)
        #     line.price_unit -= descuento_subtotal
        # for line in self.invoice_line_ids:
        #     line.update(line._get_price_total_and_subtotal_model(line.price_unit, line.quantity, line.discount,
        #                                                     line.currency_id,line.product_id, line.partner_id,
        #                                                     line.tax_ids, line.move_id.type))
        #     print('subtotal linea: ', line.price_subtotal)

        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())


        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id

            if move.is_invoice(include_receipts=True):
                handle_price_include = True
                sign = -1 if move.is_inbound() else 1
                quantity = base_line.quantity

                # price_unit_wo_discount = sign * (base_line.price_unit * base_line.quantity) * (1 - (base_line.discount / 100.0))
                price_unit_wo_discount = sign * (base_line.price_unit) * (1 - (base_line.discount / 100.0))


                tax_type = 'sale' if move.type.startswith('out_') else 'purchase'
                is_refund = move.type in ('out_refund', 'in_refund')
            else:
                handle_price_include = False
                quantity = 1.0
                price_unit_wo_discount = base_line.amount_currency if base_line.currency_id else base_line.balance
                tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
                is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)

            # print('ENCONTRO AL DESGRACIADO!!')
            descuento = base_line.monto_descuento_por_linea()
            # print('price_unit_wo_discount - quantity - descuento: ', price_unit_wo_discount, ' - ', quantity, ' - ', descuento)
            balance_taxes_res = base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
                price_unit_wo_discount,
                currency=base_line.currency_id or base_line.company_currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=is_refund,
                handle_price_include=handle_price_include,
                descuento_add=descuento,
            )

            if move.type == 'entry':
                repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
                repartition_tags = base_line.tax_ids.flatten_taxes_hierarchy().mapped(repartition_field).filtered(lambda x: x.repartition_type == 'base').tag_ids
                tags_need_inversion = self._tax_tags_need_inversion(move, is_refund, tax_type)
                if tags_need_inversion:
                    balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
                    for tax_res in balance_taxes_res['taxes']:
                        tax_res['tag_ids'] = base_line._revert_signed_tags(self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

            return balance_taxes_res

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        if not recompute_tax_base_amount:
            self.line_ids -= to_remove

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                if not recompute_tax_base_amount:
                    line.tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
            if not recompute_tax_base_amount:
                line.tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

            tax_exigible = True
            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                if tax.tax_exigibility == 'on_payment':
                    tax_exigible = False

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['amount'] += tax_vals['amount']
                taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
                taxes_map_entry['grouping_dict'] = grouping_dict
            if not recompute_tax_base_amount:
                line.tax_exigible = tax_exigible

        # ==== Pre-process taxes_map ====
        taxes_map = self._preprocess_taxes_map(taxes_map)

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            tax_line = taxes_map_entry['tax_line']

            # The tax line is no longer used in any base lines, drop it.
            if tax_line and not taxes_map_entry['grouping_dict']:
                if not recompute_tax_base_amount:
                    self.line_ids -= tax_line
                continue

            currency_id = taxes_map_entry['grouping_dict']['currency_id']
            currency = self.env['res.currency'].browse(currency_id) if currency_id else False
            conversion_date = self.date or fields.Date.context_today(self)

            # Don't create tax lines with zero balance.
            if (currency or self.company_currency_id).is_zero(taxes_map_entry['amount']):
                if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            # tax_base_amount field is expressed using the company currency.
            if currency:
                tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, conversion_date)
            else:
                tax_base_amount = taxes_map_entry['tax_base_amount']

            # Recompute only the tax_base_amount.
            if recompute_tax_base_amount:
                if taxes_map_entry['tax_line']:
                    taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
                continue

            if currency:
                amount_currency = taxes_map_entry['amount']
                balance = currency._convert(amount_currency, self.company_currency_id, self.company_id, conversion_date)
            else:
                amount_currency = 0.0
                balance = taxes_map_entry['amount']

            to_write_on_line = {
                'amount_currency': amount_currency,
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
                'tax_base_amount': tax_base_amount,
            }

            if taxes_map_entry['tax_line']:
                # Update an existing tax line.
                if tax_rep_lines_to_recompute and taxes_map_entry['tax_line'].tax_repartition_line_id not in tax_rep_lines_to_recompute:
                    continue

                taxes_map_entry['tax_line'].update(to_write_on_line)
            else:
                # Create a new tax line.
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)

                if tax_rep_lines_to_recompute and tax_repartition_line not in tax_rep_lines_to_recompute:
                    continue

                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                taxes_map_entry['tax_line'] = create_method({
                    **to_write_on_line,
                    'name': tax.name,
                    'move_id': self.id,
                    'company_id': self.company_id.id,
                    'company_currency_id': self.company_id.currency_id.id,
                    'quantity': 1.0,
                    'date_maturity': False,
                    'exclude_from_invoice_tab': True,
                    'tax_exigible': tax.tax_exigibility == 'on_invoice',
                    **taxes_map_entry['grouping_dict'],
                })

            if in_draft_mode:
                taxes_map_entry['tax_line']._onchange_amount_currency()
                taxes_map_entry['tax_line']._onchange_balance()

class SDAccountTax(models.Model):
    _inherit = 'account.tax'

    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False, handle_price_include=True, descuento_add=None):
        """ Returns all information required to apply taxes (in self + their children in case of a tax group).
            We consider the sequence of the parent for group of taxes.
                Eg. considering letters as taxes and alphabetic order as sequence :
                [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]

            'handle_price_include' is used when we need to ignore all tax included in price. If False, it means the
            amount passed to this method will be considered as the base of all computations.

        RETURN: {
            'total_excluded': 0.0,    # Total without taxes
            'total_included': 0.0,    # Total with taxes
            'total_void'    : 0.0,    # Total with those taxes, that don't have an account set
            'taxes': [{               # One dict for each tax in self and their children
                'id': int,
                'name': str,
                'amount': float,
                'sequence': int,
                'account_id': int,
                'refund_account_id': int,
                'analytic': boolean,
            }],
        } """
        if not self:
            company = self.env.company
        else:
            company = self[0].company_id

        # 1) Flatten the taxes.
        taxes, groups_map = self.flatten_taxes_hierarchy(create_map=True)

        # 2) Avoid mixing taxes having price_include=False && include_base_amount=True
        # with taxes having price_include=True. This use case is not supported as the
        # computation of the total_excluded would be impossible.
        base_excluded_flag = False  # price_include=False && include_base_amount=True
        included_flag = False  # price_include=True
        for tax in taxes:
            if tax.price_include:
                included_flag = True
            elif tax.include_base_amount:
                base_excluded_flag = True
            if base_excluded_flag and included_flag:
                raise UserError(_('Unable to mix any taxes being price included with taxes affecting the base amount but not included in price.'))

        # 3) Deal with the rounding methods
        if not currency:
            currency = company.currency_id

        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line
        prec = currency.rounding

        # In some cases, it is necessary to force/prevent the rounding of the tax and the total
        # amounts. For example, in SO/PO line, we don't want to round the price unit at the
        # precision of the currency.
        # The context key 'round' allows to force the standard behavior.
        round_tax = False if company.tax_calculation_rounding_method == 'round_globally' else True
        if 'round' in self.env.context:
            round_tax = bool(self.env.context['round'])

        if not round_tax:
            prec *= 1e-5

        # 4) Iterate the taxes in the reversed sequence order to retrieve the initial base of the computation.
        #     tax  |  base  |  amount  |
        # /\ ----------------------------
        # || tax_1 |  XXXX  |          | <- we are looking for that, it's the total_excluded
        # || tax_2 |   ..   |          |
        # || tax_3 |   ..   |          |
        # ||  ...  |   ..   |    ..    |
        #    ----------------------------
        def recompute_base(base_amount, fixed_amount, percent_amount, division_amount):
            # Recompute the new base amount based on included fixed/percent amounts and the current base amount.
            # Example:
            #  tax  |  amount  |   type   |  price_include  |
            # -----------------------------------------------
            # tax_1 |   10%    | percent  |  t
            # tax_2 |   15     |   fix    |  t
            # tax_3 |   20%    | percent  |  t
            # tax_4 |   10%    | division |  t
            # -----------------------------------------------

            # if base_amount = 145, the new base is computed as:
            # (145 - 15) / (1.0 + 30%) * 90% = 130 / 1.3 * 90% = 90
            return (base_amount - fixed_amount) / (1.0 + percent_amount / 100.0) * (100 - division_amount) / 100

        # The first/last base must absolutely be rounded to work in round globally.
        # Indeed, the sum of all taxes ('taxes' key in the result dictionary) must be strictly equals to
        # 'price_included' - 'price_excluded' whatever the rounding method.
        #
        # Example using the global rounding without any decimals:
        # Suppose two invoice lines: 27000 and 10920, both having a 19% price included tax.
        #
        #                   Line 1                      Line 2
        # -----------------------------------------------------------------------
        # total_included:   27000                       10920
        # tax:              27000 / 1.19 = 4310.924     10920 / 1.19 = 1743.529
        # total_excluded:   22689.076                   9176.471
        #
        # If the rounding of the total_excluded isn't made at the end, it could lead to some rounding issues
        # when summing the tax amounts, e.g. on invoices.
        # In that case:
        #  - amount_untaxed will be 22689 + 9176 = 31865
        #  - amount_tax will be 4310.924 + 1743.529 = 6054.453 ~ 6054
        #  - amount_total will be 31865 + 6054 = 37919 != 37920 = 27000 + 10920
        #
        # By performing a rounding at the end to compute the price_excluded amount, the amount_tax will be strictly
        # equals to 'price_included' - 'price_excluded' after rounding and then:
        #   Line 1: sum(taxes) = 27000 - 22689 = 4311
        #   Line 2: sum(taxes) = 10920 - 2176 = 8744
        #   amount_tax = 4311 + 8744 = 13055
        #   amount_total = 31865 + 13055 = 37920
        # print('descuento !!: ', descuento_add)
        # print('entro al compute_all')
        if not descuento_add:
            descuento_add = 0
        else:
            if price_unit < 0:
                descuento_add *= -1

        base = currency.round((price_unit * quantity) - descuento_add)
        # print('base: ', base)
        # For the computation of move lines, we could have a negative base value.
        # In this case, compute all with positive values and negate them at the end.
        sign = 1
        if currency.is_zero(base):
            sign = self._context.get('force_sign', 1)
        elif base < 0:
            sign = -1
        if base < 0:
            base = -base

        # Store the totals to reach when using price_include taxes (only the last price included in row)
        total_included_checkpoints = {}
        i = len(taxes) - 1
        store_included_tax_total = True
        # Keep track of the accumulated included fixed/percent amount.
        incl_fixed_amount = incl_percent_amount = incl_division_amount = 0
        # Store the tax amounts we compute while searching for the total_excluded
        cached_tax_amounts = {}
        if handle_price_include:
            for tax in reversed(taxes):
                tax_repartition_lines = (
                    is_refund
                    and tax.refund_repartition_line_ids
                    or tax.invoice_repartition_line_ids
                ).filtered(lambda x: x.repartition_type == "tax")
                sum_repartition_factor = sum(tax_repartition_lines.mapped("factor"))

                if tax.include_base_amount:
                    base = recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount)
                    incl_fixed_amount = incl_percent_amount = incl_division_amount = 0
                    store_included_tax_total = True
                if tax.price_include or self._context.get('force_price_include'):
                    if tax.amount_type == 'percent':
                        incl_percent_amount += tax.amount * sum_repartition_factor
                    elif tax.amount_type == 'division':
                        incl_division_amount += tax.amount * sum_repartition_factor
                    elif tax.amount_type == 'fixed':
                        incl_fixed_amount += quantity * tax.amount * sum_repartition_factor
                    else:
                        # tax.amount_type == other (python)
                        tax_amount = tax._compute_amount(base, sign * price_unit, abs(quantity), product, partner) * sum_repartition_factor
                        incl_fixed_amount += tax_amount
                        # Avoid unecessary re-computation
                        cached_tax_amounts[i] = tax_amount
                    # In case of a zero tax, do not store the base amount since the tax amount will
                    # be zero anyway. Group and Python taxes have an amount of zero, so do not take
                    # them into account.
                    if store_included_tax_total and (
                        tax.amount or tax.amount_type not in ("percent", "division", "fixed")
                    ):
                        total_included_checkpoints[i] = base
                        store_included_tax_total = False
                i -= 1

        total_excluded = currency.round(recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount))
        # print('total_excluded: ', total_excluded)
        # total_excluded -= descuento_add
        # 5) Iterate the taxes in the sequence order to compute missing tax amounts.
        # Start the computation of accumulated amounts at the total_excluded value.
        base = total_included = total_void = total_excluded

        taxes_vals = []
        i = 0
        cumulated_tax_included_amount = 0
        for tax in taxes:
            tax_repartition_lines = (is_refund and tax.refund_repartition_line_ids or tax.invoice_repartition_line_ids).filtered(lambda x: x.repartition_type == 'tax')
            sum_repartition_factor = sum(tax_repartition_lines.mapped('factor'))

            price_include = self._context.get('force_price_include', tax.price_include)

            #compute the tax_amount
            if price_include and total_included_checkpoints.get(i) is not None and sum_repartition_factor != 0:
                # We know the total to reach for that tax, so we make a substraction to avoid any rounding issues
                tax_amount = total_included_checkpoints[i] - (base + cumulated_tax_included_amount)
                cumulated_tax_included_amount = 0
            else:
                tax_amount = tax.with_context(force_price_include=False)._compute_amount(
                    base, sign * price_unit, quantity, product, partner)

            # Round the tax_amount multiplied by the computed repartition lines factor.
            tax_amount = round(tax_amount, precision_rounding=prec)
            factorized_tax_amount = round(tax_amount * sum_repartition_factor, precision_rounding=prec)

            if price_include and total_included_checkpoints.get(i) is None:
                cumulated_tax_included_amount += factorized_tax_amount

            # If the tax affects the base of subsequent taxes, its tax move lines must
            # receive the base tags and tag_ids of these taxes, so that the tax report computes
            # the right total
            subsequent_taxes = self.env['account.tax']
            subsequent_tags = self.env['account.account.tag']
            if tax.include_base_amount:
                subsequent_taxes = taxes[i+1:]
                subsequent_tags = subsequent_taxes.get_tax_tags(is_refund, 'base')

            # Compute the tax line amounts by multiplying each factor with the tax amount.
            # Then, spread the tax rounding to ensure the consistency of each line independently with the factorized
            # amount. E.g:
            #
            # Suppose a tax having 4 x 50% repartition line applied on a tax amount of 0.03 with 2 decimal places.
            # The factorized_tax_amount will be 0.06 (200% x 0.03). However, each line taken independently will compute
            # 50% * 0.03 = 0.01 with rounding. It means there is 0.06 - 0.04 = 0.02 as total_rounding_error to dispatch
            # in lines as 2 x 0.01.
            repartition_line_amounts = [round(tax_amount * line.factor, precision_rounding=prec) for line in tax_repartition_lines]
            total_rounding_error = round(factorized_tax_amount - sum(repartition_line_amounts), precision_rounding=prec)
            nber_rounding_steps = int(abs(total_rounding_error / currency.rounding))
            rounding_error = round(nber_rounding_steps and total_rounding_error / nber_rounding_steps or 0.0, precision_rounding=prec)

            for repartition_line, line_amount in zip(tax_repartition_lines, repartition_line_amounts):

                if nber_rounding_steps:
                    line_amount += rounding_error
                    nber_rounding_steps -= 1

                taxes_vals.append({
                    'id': tax.id,
                    'name': partner and tax.with_context(lang=partner.lang).name or tax.name,
                    'amount': sign * line_amount,
                    'base': round(sign * base, precision_rounding=prec),
                    'sequence': tax.sequence,
                    'account_id': tax.cash_basis_transition_account_id.id if tax.tax_exigibility == 'on_payment' else repartition_line.account_id.id,
                    'analytic': tax.analytic,
                    'price_include': price_include,
                    'tax_exigibility': tax.tax_exigibility,
                    'tax_repartition_line_id': repartition_line.id,
                    'group': groups_map.get(tax),
                    'tag_ids': (repartition_line.tag_ids + subsequent_tags).ids,
                    'tax_ids': subsequent_taxes.ids,
                })

                if not repartition_line.account_id:
                    total_void += line_amount

            # Affect subsequent taxes
            if tax.include_base_amount:
                base += factorized_tax_amount

            total_included += factorized_tax_amount
            i += 1

        # print('total_excluded: ', total_excluded)
        # print('total_includded: ', total_included)
        return {
            'base_tags': taxes.mapped(is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids').filtered(lambda x: x.repartition_type == 'base').mapped('tag_ids').ids,
            'taxes': taxes_vals,
            'total_excluded': (sign * total_excluded),
            'total_included': (sign * currency.round(total_included)),
            'total_void': sign * currency.round(total_void),
        }
