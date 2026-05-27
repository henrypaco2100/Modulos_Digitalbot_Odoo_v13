 # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import fields, models, api, _
import datetime
from odoo.exceptions import UserError
    #DAVID MODELO HEREDADO PARA PODER AGREGAR BOTON A LA VISTA DE COMPRAS


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # landed_costs_ids_purchase = fields.One2many('stock.landed.cost', 'vendor_bill_id', string='Landed Costs')

    landed_costs_ids_count = fields.Integer(string='Invoice Count', compute='_get_lc_cost', readonly=True)
    landed_costs_ids_purchase = fields.Many2many("stock.landed.cost", string='Costes de Destinos',copy=False)

    @api.depends('landed_costs_ids_purchase')
    def _get_lc_cost(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.search([
        #             ('alert_date', '<=', fields.Date.today()),
        #             ('product_expiry_reminded', '=', False)])([('share', '=' , False)], limit=10, order='id desc')
        # stock_lc_ids = self.env['stock.landed.cost'].search([('vendor_bill_id.name', '=', self.invoice_ids.name)],
        #                                                     limit=1)
        # stock_lc_ids = self.env['stock.landed.cost'].search([('id', 'in',[factura.id for factura in self.invoice_ids])],)
        self.landed_costs_ids_count = len(self.landed_costs_ids_purchase)


    def button_create_lc(self):
        # self.ensure_one() #david
        self.verificar_factura_publicada()
        date_transferencia = self.get_transferencia()
        invoice_lc = self.env['account.move'].search([('id', 'in',[factura.id for factura in self.invoice_ids.filtered(lambda x: x.state == 'posted')] )],limit=1,order='id desc')
        date_lc = datetime.datetime.now()
        picking_lc = self.picking_ids.ids
        if date_transferencia and picking_lc and invoice_lc:
            vals = {
                'date': date_transferencia,
                'sd_date': date_transferencia,
                'picking_ids': picking_lc,
                'vendor_bill_id': invoice_lc.id,
                'state': 'draft',
            }

            landed_cost_id = self.env['stock.landed.cost'].sudo().create(vals)
            print('landed_cost_id:', landed_cost_id)
            self.write({
                'landed_costs_ids_purchase' : [(4, landed_cost_id.id)],
            })
        return self.action_view_lc()

    def get_transferencia(self):
        picking_ids = self.picking_ids.filtered(lambda l: l.state=='done' and l.picking_type_id.code=='incoming')
        for picking in picking_ids:
            return picking.date_done

    def verificar_factura_publicada(self):
       if not len(self.invoice_ids.filtered(lambda x: x.state == 'posted'))>=1:
           raise UserError(_("Es Necesario publicar una factura para continuar."))

    def action_view_lc(self):
        self.ensure_one()
        if len(self.landed_costs_ids_purchase.ids) != 1:
            return {
                'name': _('Coste de Importacion'),
                'view_mode': 'tree,form',
                'res_model': 'stock.landed.cost',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', self.landed_costs_ids_purchase.ids)],
            }
        elif len(self.landed_costs_ids_purchase.ids) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.landed.cost',
                'view_mode': 'form',
                'views': [[self.env.ref('stock_landed_costs.view_stock_landed_cost_form').id, 'form']],
                'res_id': self.landed_costs_ids_purchase.id,
                'target': 'current',
            }