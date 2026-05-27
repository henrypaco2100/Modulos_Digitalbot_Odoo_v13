from odoo import api, models, _
from odoo.exceptions import UserError

class PosInvoiceReportSiat(models.AbstractModel):
    _name = 'report.sd_facturacion_en_linea_correo_v13.report_rollo'
    _description = 'report roll of point of sale'

    @api.model
    def _get_report_values(self, docids, data=None):
#         print('name: ', self._name)
#         PosOrder = self.env['pos.order']
#         ids_to_print = []
#         invoiced_posorders_ids = []
#         selected_orders = PosOrder.browse(docids)
#         for order in selected_orders.filtered(lambda o: o.account_move):
#             ids_to_print.append(order.account_move.id)
#             invoiced_posorders_ids.append(order.id)
#         not_invoiced_orders_ids = list(set(docids) - set(invoiced_posorders_ids))
#         if not_invoiced_orders_ids:
#             not_invoiced_posorders = PosOrder.browse(not_invoiced_orders_ids)
#             not_invoiced_orders_names = [a.name for a in not_invoiced_posorders]
#             raise UserError(_('No link to an invoice for %s.') % ', '.join(not_invoiced_orders_names))

#         print('docs: ', docids)

        return {'docs': self.env['account.move'].search([('id', 'in', docids)])}


class InvoiceReportSiat(models.AbstractModel):
    _name = 'report.sd_facturacion_en_linea_correo_v13.report_rollo_pos'
    _description = 'report roll of point of sale'

    @api.model
    def _get_report_values(self, docids, data=None):
        # print('name: ', self._name)
        PosOrder = self.env['pos.order']
        ids_to_print = []
        invoiced_posorders_ids = []
        selected_orders = PosOrder.browse(docids)
        for order in selected_orders.filtered(lambda o: o.account_move):
            ids_to_print.append(order.account_move.id)
            invoiced_posorders_ids.append(order.id)
        not_invoiced_orders_ids = list(set(docids) - set(invoiced_posorders_ids))
        if not_invoiced_orders_ids:
            not_invoiced_posorders = PosOrder.browse(not_invoiced_orders_ids)
            not_invoiced_orders_names = [a.name for a in not_invoiced_posorders]
            raise UserError(_('No link to an invoice for %s.') % ', '.join(not_invoiced_orders_names))

        return {'docs': self.env['account.move'].search([('id', 'in', ids_to_print)])}
