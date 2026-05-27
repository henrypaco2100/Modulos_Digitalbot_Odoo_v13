# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools

class sale(models.Model):
    _inherit = 'sale.order'

    def action_cancel(self):
        self.update({
            'st_orden_cancelada': True
        })
        """
        Cancel order,invoice and picking, and inventory valuation
        """
        pickings= self.picking_ids
        if pickings:
            for picking in pickings:
                picking.action_cancel()

        facturas= self.invoice_ids
        if facturas:
            for factura in facturas:
                payment_ids = factura.get_payment_out_invoice()
                if payment_ids:
                    payment_ids.action_draft()
                    payment_ids.cancel()
                #Henry
                if factura.state == 'draft':
                    factura.button_cancel()
                elif factura.state == 'posted':
                    factura.button_draft()
                    factura.button_cancel()
        return super(sale, self).action_cancel()

