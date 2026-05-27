from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare

from datetime import datetime

class InheritProductProduceSodigitalim(models.TransientModel):
    _inherit = 'mrp.product.produce'

    def do_produce(self):
        """ Save the current wizard and go back to the MO. """
        self.ensure_one()
        self.validar_lot_id_()
        self._record_production()
        self._check_company()
        self.rellenar_move_line_ids()
        return {'type': 'ir.actions.act_window_close'}

    def validar_lot_id_(self):
        lineas_componentes =self.raw_workorder_line_ids or self.finished_workorder_line_ids
        if lineas_componentes:
            for lineas in lineas_componentes:
                if lineas.product_id.tracking == 'lot':
                    if not lineas.lot_id:
                        raise UserError(
                            _('Es Necesario el "Lote/Nº de serie en todas las filas de los Componentes".'))


    def rellenar_move_line_ids(self):
        if self.production_id:
            if not len(self.production_id.finished_move_line_ids) > 1:
                lot_production_id = self.production_id.finished_move_line_ids.lot_id
                for move_raw_id in self.production_id.move_raw_ids:
                    for move_line_id in move_raw_id.move_line_ids:
                        if not move_line_id.lot_produced_ids:
                            move_line_id.write({
                                'lot_produced_ids':lot_production_id,
                            })


class InheritProductProducelineSodigitalim(models.TransientModel):
    _inherit = 'mrp.product.produce.line'

    @api.onchange('lot_id')
    def verificar_stock_lote_product(self):
        if self.product_id.tracking == 'lot':
            if not self.lot_id.product_qty >= self.qty_done:
                self.write({
                    'lot_id':None,
                })
                self.lot_id = ''
                return {
                    'warning': {
                        'message': _(
                            f'Stock del Lote insuficiente, Elija Otro lote o Modifique la cantidad de la columna "Consumido". ')
                    }
                }

    @api.onchange('qty_done')
    def verificar_stock_lote_product(self):
        if self.product_id.tracking == 'lot':
            if not self.lot_id.product_qty >= self.qty_done:
                self.write({
                    'lot_id': None,
                })
                self.qty_done = 0
                self.lot_id = ''
                return {
                    'warning': {
                        'message': _(
                            f'Stock del Lote insuficiente, Elija Otro lote o Modifique la cantidad de la columna "Consumido". ')
                    }
                }
