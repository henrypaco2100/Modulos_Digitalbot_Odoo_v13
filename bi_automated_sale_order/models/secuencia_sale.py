# -*- coding : utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
class SaleOrderSequence(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self,vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                # condifcion para verificar si exite el proceso automated
                if vals['work_process_order_id']:
                    objeto_automated = self.env['automated.sale'].search([('id', '=', vals['work_process_order_id'])])
                    vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id'],ir_sequence_date=vals['date_order']).next_by_code(objeto_automated.st_secuencia_quotation.code) or _('New')
                else:
                    vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id'],ir_sequence_date=vals['date_order']).next_by_code(
                        'sale.quotation') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].with_context(ir_sequence_date=vals['date_order']).next_by_code('sale.quotation') or _('New')

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id',
                                                   partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(SaleOrderSequence, self).create(vals)
        return result

    # def action_confirm(self):
    #     if self.work_process_order_id.st_secuencia.code:
    #         self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.date_order).next_by_code(self.work_process_order_id.st_secuencia.code) or _('New')
    #     else:
    #         self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.date_order).next_by_code('sale.order') or _('New')
    #     result = super(SaleOrderSequence, self).action_confirm()
    #     return result

    def action_confirm(self):
        if self.work_process_order_id.st_secuencia.code:
            self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.date_order).next_by_code(self.work_process_order_id.st_secuencia.code) or _('New')
        elif self.work_process_order_id.st_secuencia_quotation.code:
            return super(SaleOrderSequence, self).action_confirm()
        else:
            self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.date_order).next_by_code('sale.order') or _('New')
        result = super(SaleOrderSequence, self).action_confirm()

        return result

    def update_sequences(self):
        cam = self.env['ir.model.data'].get_object_reference('sale', 'seq_sale_order')[1]
        cad = self.env['ir.model.data'].get_object_reference('bi_automated_sale_order', 'seq_sale_quotation')[1]
        if self.state == 'sale':
            self.sequences = cam

        else:
            self.sequences = cad
class SequencePicking(models.Model):
    _inherit = 'stock.picking'
    @api.model
    def create(self, vals):
        defaults = self.default_get(['name', 'picking_type_id'])
        picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id')))
        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id', defaults.get('picking_type_id')):
            if picking_type.sequence_id:
                # Henry Codigo para modificar fecha y correcion para duplicar transferencia
                if len(vals) >= 9:
                    scheduled_date = vals.get('scheduled_date', False)
                    if picking_type.code == 'internal':
                        # arreglar
                        if scheduled_date:
                            vals['name'] = picking_type.sequence_id.with_context(ir_sequence_date=scheduled_date).next_by_id()
                        else:
                            vals['name'] = picking_type.sequence_id.with_context(ir_sequence_date=fields.Datetime.now()).next_by_id()
                    # else:
                    #     raise Warning(('Usted no tiene permiso para realizar este tipo de operacion, solo puede realizar Transferencias Internas'))

                elif picking_type.code == 'incoming':

                    vals['name'] = picking_type.sequence_id.with_context(ir_sequence_date= vals['date']).next_by_id()
                elif picking_type.code == 'outgoing':
                    objeto_order_sale= self.env['sale.order'].search([('name','=',vals['origin'] )])
                    vals['name'] = picking_type.sequence_id.with_context(ir_sequence_date=objeto_order_sale.date_order).next_by_id()
        # As the on_change in one2many list is WIP, we will overwrite the locations on the stock moves here
        # As it is a create the format will be a list of (0, 0, dict)
        moves = vals.get('move_lines', []) + vals.get('move_ids_without_package', [])
        if moves and vals.get('location_id') and vals.get('location_dest_id'):
            for move in moves:
                if len(move) == 3 and move[0] == 0:
                    move[2]['location_id'] = vals['location_id']
                    move[2]['location_dest_id'] = vals['location_dest_id']
                    # When creating a new picking, a move can have no `company_id` (create before
                    # picking type was defined) or a different `company_id` (the picking type was
                    # changed for an another company picking type after the move was created).
                    # So, we define the `company_id` in one of these cases.
                    picking_type = self.env['stock.picking.type'].browse(vals['picking_type_id'])
                    if 'picking_type_id' not in move[2] or move[2]['picking_type_id'] != picking_type.id:
                        move[2]['picking_type_id'] = picking_type.id
                        move[2]['company_id'] = picking_type.company_id.id
        # make sure to write `schedule_date` *after* the `stock.move` creation in
        # order to get a determinist execution of `_set_scheduled_date`
        scheduled_date = vals.get('scheduled_date', False)
        res = super(SequencePicking, self).create(vals)
        if scheduled_date:
            res.with_context(mail_notrack=True).write({'scheduled_date': scheduled_date})
        res._autoconfirm_picking()

        # set partner as follower
        if vals.get('partner_id'):
            for picking in res.filtered(lambda p: p.location_id.usage == 'supplier' or p.location_dest_id.usage == 'customer'):
                picking.message_subscribe([vals.get('partner_id')])

        return res