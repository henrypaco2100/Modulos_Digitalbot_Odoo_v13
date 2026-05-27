from odoo import api, fields, models, _
from datetime import date,datetime,timedelta
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

class inherit_Account_move(models.Model):
    _inherit = 'account.move'

    #factura venta
    fcb_codigo_de_control = fields.Char(string="Código de Control", readonly=True)
    fcb_numero_factura_computarizada = fields.Char(string='Nº de Factura Computarizada', readonly=True)
    fcb_es_computarizado = fields.Boolean(related='journal_id.fcb_es_computarizado',default=False,string='Computarizada')
    fcb_nit_a_facturar = fields.Char(string ='Nit')
    fcb_nombre_a_facturar = fields.Char(string='Nombre a Facturar')

    #invoice_date = fields.Date(required=True)

    #factura compra
    fcb_autorizacion_compra = fields.Char(string="Numero de Autorizacion")
    fcb_codigo_control_compra = fields.Char(string="Codigo de Control")
    fcb_numero_dim = fields.Char(string="Numero de Declaracion de Importacion")
    fcb_tipo_compra = fields.Selection([
        ('compra_interno_gravadas', 'Compras para mercado interno con destino a actividades gravadas'),
        ('compra_interno_no_gravadas', 'Compras para mercado interno con destino a actividades no gravadas,'),
        ('compra_proporcionalidad', 'Compras sujetas a proporcionalidad'),
        ('compra_exportaciones', 'Compras para exportaciones'),
        ('compra_interno_exportaciones', 'Compras tanto para el mercado interno como para exportaciones'),
        ],
        string='Factura de Compras')


    #FACTURA COMPUTARIZADA
    met_pago = fields.Selection([
        ('1', 'Pago en efectivo'),
        ('2', 'Credito'),
        ('3', 'Tarjeta'),
        ],
        string='Metodo de Pago')

    cuf_id = fields.Char("CUF", help="Codigo unico de Facturacion de Impuesto Nacionales")

    cufd_id = fields.Char("CUFD", help="Codigo unico de Facturacion Diaria de Impuestos Nacionales")

    def post(self):
        # `user_has_group` won't be bypassed by `sudo()` since it doesn't change the user anymore.
        if not self.env.su and not self.env.user.has_group('account.group_account_invoice'):
            raise AccessError(_("You don't have the access rights to post an invoice."))
        if self.type == 'out_invoice':
            # es computarizado el Diario
            if self.journal_id.fcb_fecha_limite_emision:
                if self.invoice_date:
                    if self.invoice_date > self.journal_id.fcb_fecha_limite_emision:
                        raise UserError(_("Dosificacion Caducado, no es posible Publicar la Factura"))
                else:
                    raise UserError(
                        _('Para Crear una Factura Computarizada es necesario el campo "Fecha Factura" .'))
        for move in self:
            if not move.line_ids.filtered(lambda line: not line.display_type):
                raise UserError(_('You need to add a line before posting.'))
            if move.auto_post and move.date > fields.Date.today():
                date_msg = move.date.strftime(get_lang(self.env).date_format)
                raise UserError(_("This move is configured to be auto-posted on %s" % date_msg))

            if not move.partner_id:
                if move.is_sale_document():
                    raise UserError(
                        _("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
                elif move.is_purchase_document():
                    raise UserError(
                        _("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

            if move.is_invoice(include_receipts=True) and float_compare(move.amount_total, 0.0,
                                                                        precision_rounding=move.currency_id.rounding) < 0:
                raise UserError(_(
                    "You cannot validate an invoice with a negative total amount. You should create a credit note instead. Use the action menu to transform it into a credit note or refund."))

            # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
            # lines are recomputed accordingly.
            # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
            # environment.
            if not move.invoice_date and move.is_invoice(include_receipts=True):
                move.invoice_date = fields.Date.context_today(self)
                move.with_context(check_move_validity=False)._onchange_invoice_date()

            # When the accounting date is prior to the tax lock date, move it automatically to the next available date.
            # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
            # environment.
            if (move.company_id.tax_lock_date and move.date <= move.company_id.tax_lock_date) and (
                    move.line_ids.tax_ids or move.line_ids.tag_ids):
                move.date = move.company_id.tax_lock_date + timedelta(days=1)
                move.with_context(check_move_validity=False)._onchange_currency()

        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        self.mapped('line_ids').create_analytic_lines()
        for move in self:
            if move.auto_post and move.date > fields.Date.today():
                raise UserError(_("This move is configured to be auto-posted on {}".format(
                    move.date.strftime(get_lang(self.env).date_format))))

            move.message_subscribe([p.id for p in [move.partner_id] if p not in move.sudo().message_partner_ids])

            to_write = {'state': 'posted'}

            if move.name == '/':
                # Get the journal's sequence.
                sequence = move._get_sequence()
                if not sequence:
                    raise UserError(_('Please define a sequence on your journal.'))

                # Consume a new number.
                to_write['name'] = sequence.with_context(ir_sequence_date=move.date).next_by_id()

            move.write(to_write)

            # Compute 'ref' for 'out_invoice'.
            if move.type == 'out_invoice' and not move.invoice_payment_ref:
                to_write = {
                    'invoice_payment_ref': move._get_invoice_computed_reference(),
                    'line_ids': []
                }
                for line in move.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
                    to_write['line_ids'].append((1, line.id, {'name': to_write['invoice_payment_ref']}))
                move.write(to_write)

            if move == move.company_id.account_opening_move_id and not move.company_id.account_bank_reconciliation_start:
                # For opening moves, we set the reconciliation date threshold
                # to the move's date if it wasn't already set (we don't want
                # to have to reconcile all the older payments -made before
                # installing Accounting- with bank statements)
                move.company_id.account_bank_reconciliation_start = move.date

        for move in self:
            if not move.partner_id: continue
            if move.type.startswith('out_'):
                move.partner_id._increase_rank('customer_rank')
            elif move.type.startswith('in_'):
                move.partner_id._increase_rank('supplier_rank')
            else:
                continue

        # Trigger action for paid invoices in amount is zero
        self.filtered(
            lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
        ).action_invoice_paid()

        # Force balance check since nothing prevents another module to create an incorrect entry.
        # This is performed at the very end to avoid flushing fields before the whole processing.
        self._check_balanced()

        # para generar el codigo de control y numero factura
        if self.type == 'out_invoice':
            if self.journal_id.fcb_es_computarizado:
                pertenece_grupo = self.env['res.users'].has_group(
                    'st_facturacion_computarizada_bolivia_v13.group_invoice_move_computer_bolivia')
                if pertenece_grupo:
                    nit_factura = self.fcb_nit_a_facturar or self.partner_id.vat
                    if self.invoice_date:
                        action_jurnal = self.env['facturacion.computarizada.bolivia']
                        if not self.fcb_numero_factura_computarizada:
                            codigo_de_control=action_jurnal.generar_codigo_control(self.invoice_date, self.journal_id.fcb_siguiente_Numero,
                                                                                   nit_factura,self.journal_id.fcb_numero_autorizacion_diario,
                                                                                   self.journal_id.fcb_llave_de_dosificacion,self.amount_total)
                            numero_factura_computarizada = self.journal_id.concatenar_ceros_numero_factura(self.journal_id.fcb_siguiente_Numero)
                            self.write({
                                'fcb_codigo_de_control':codigo_de_control,
                                'fcb_numero_factura_computarizada': numero_factura_computarizada
                            })
                            # Incrementar Numero siguiente
                            self.journal_id.incrementar_siguiente_numero_factura_computarizada()
                        else:
                            codigo_de_control = action_jurnal.generar_codigo_control(self.invoice_date,
                                                                                     self.journal_id.fcb_siguiente_Numero,
                                                                                     nit_factura,
                                                                                     self.fcb_numero_factura_computarizada,
                                                                                     self.journal_id.fcb_llave_de_dosificacion,
                                                                                     self.amount_total)
                            self.write({'fcb_codigo_de_control': codigo_de_control,})


                    else :
                        raise UserError(
                            _('Para Crear una Factura Computarizada es necesario el campo "Fecha Factura" .'))
                else:
                    raise UserError(
                        _('No tiene permiso para Publicar factura tipo Computarizada.'))
        # cargar datos automatizacion factura computarizada compra
        if self.type == 'in_invoice':
            if self.invoice_origin:
                objeto_pedido_compra = self.env['purchase.order'].search([('name', '=', self.invoice_origin)])

                self.write({
                    'fcb_autorizacion_compra': objeto_pedido_compra.fcb_autorizacion_compra_order,
                    'fcb_codigo_control_compra': objeto_pedido_compra.fcb_codigo_control_compra_order,
                    'fcb_numero_dim': objeto_pedido_compra.fcb_numero_dim_order,
                    'fcb_tipo_compra': objeto_pedido_compra.fcb_tipo_compra_order,
                })

        return True
    @api.onchange('fcb_autorizacion_compra')
    def maximo_caracteres(self):

        caracteres=self.fcb_autorizacion_compra
        diccionario_numerico={'0','1','2','3','4','5','6','7','8','9'}
        if caracteres:
            for i in caracteres:
                if not i in diccionario_numerico:
                    self.fcb_autorizacion_compra=''
                    return {
                        'warning': {
                            'message': _(
                                f'Se permiten solo caracteres numérico en el campo: "Fecha de Activación", porfavor vuelva a intentarlo!!. ')
                        }
                    }

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



