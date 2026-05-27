from odoo import models, api,fields

class SdInheritAccountMoveCancel(models.Model):
    _inherit = 'account.move'
    def get_payment_out_invoice(self):
        """Obtener Pagos"""
        payment_ids = self.env['account.payment']
        pay_term_line_ids = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        partials = pay_term_line_ids.mapped('matched_debit_ids') + pay_term_line_ids.mapped('matched_credit_ids')
        for partial in partials:
            counterpart_lines = partial.debit_move_id + partial.credit_move_id
            counterpart_line = counterpart_lines.filtered(lambda line: line.id not in self.line_ids.ids)
            payment_ids += counterpart_line.payment_id
        return payment_ids


