from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime

class SdPagoFacturaMasiva(models.TransientModel):
    _name = 'account.move.wizard.pagos.factura.masiva'

    @api.model
    def default_get(self, fields):
        res = super(SdPagoFacturaMasiva, self).default_get(fields)

        siat_factura_masiva_id = self.env.context.get('default_id') or self.env.context.get('active_id')
        if siat_factura_masiva_id:
            factura_masiva = self.env['siat.emision.masiva'].browse(siat_factura_masiva_id)
        if factura_masiva.exists():
            factura_masiva.ensure_one()
            if 'siat_factura_masiva_id' in fields:
                res['siat_factura_masiva_id'] = factura_masiva.id

        return res

    siat_factura_masiva_id = fields.Many2one('siat.emision.masiva', string='Factura Masiva')
    facturas_ids = fields.One2many(related='siat_factura_masiva_id.sd_invoice_ids')
    factura_online_id = fields.Many2one(related='siat_factura_masiva_id.sd_factura_online_id')

    def action_pagar_facturas(self):
        '''Este metodo se encarga de realizar el pago de las facturas masivas'''

        self.create_payment(self.facturas_ids,datetime.now())

    def create_payment(self, invoice_obj, date_order_factura_pago):
        """ Este metodo se encarga de crear el pado de la factura"""

        # validate = invoice_obj.action_post()
        fact_online = self.factura_online_id
        payment = self.env['account.payment']
        payment_method = self.env['account.payment.method'].search([], limit=1)
        for inv in invoice_obj:
            res = payment.create({
                'partner_id': inv.partner_id.id,
                'amount': inv.amount_total,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'payment_method_id': payment_method.id,
                'journal_id': self.factura_online_id.sd_journal_id.id,
                'payment_date': date_order_factura_pago,
                'communication': inv.name + " ",
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
        mjs = fact_online.mensaje_personalizador('Se ha enviado correctamente las facturas a los correos')
        return mjs