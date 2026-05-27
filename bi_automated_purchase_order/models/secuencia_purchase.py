from odoo import api, fields, models, _


class PurchaseOrderSecuencia(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self,vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                # validacion del automated process
                if vals['work_process_order_id']:
                    objeto_automated = self.env['automated.purchase'].search(
                        [('id', '=', vals['work_process_order_id'])])
                    vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id'],ir_sequence_date=vals['date_order']).next_by_code(
                        objeto_automated.st_secuencia_quotation.code) or _('New')
                else:
                    vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id'], ir_sequence_date =vals['date_order']).next_by_code(
                        'purchase.quotation') or _('New')

            else:
                vals['name'] = self.env['ir.sequence'].with_context(ir_sequence_date =vals['date_order']).next_by_code('purchase.quotation') or _('New')

        result = super(PurchaseOrderSecuencia, self).create(vals)
        return result

    def button_confirm(self):
        if self.work_process_order_id.st_secuencia.code:
            self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.date_order).next_by_code(
                self.work_process_order_id.st_secuencia.code) or _('New')
        elif self.work_process_order_id.st_secuencia_quotation.code:
            return super(PurchaseOrderSecuencia, self).button_confirm()
        else:
            self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.date_order).next_by_code(
                'purchase.order') or _('New')
        result = super(PurchaseOrderSecuencia, self).button_confirm()

        return result

    def update_sequences(self):
        cam = self.env['ir.model.data'].get_object_reference('purchase', 'seq_purchase_order')[1]
        cad = self.env['ir.model.data'].get_object_reference('bi_automated_purchase_order', 'seq_purchase_quotation')[1]
        if self.state == 'purchase':
            self.sequence_name = cam
        else:
            self.sequence_name = cad
class SequencePickingPurchase(models.Model):
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
        res = super(SequencePickingPurchase, self).create(vals)
        if scheduled_date:
            res.with_context(mail_notrack=True).write({'scheduled_date': scheduled_date})
        res._autoconfirm_picking()

        # set partner as follower
        if vals.get('partner_id'):
            for picking in res.filtered(lambda p: p.location_id.usage == 'supplier' or p.location_dest_id.usage == 'customer'):
                picking.message_subscribe([vals.get('partner_id')])

        return res
