from odoo import api, fields, models, _
import base64
from datetime import datetime, timedelta
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import re
class SdInheritPosOrder(models.Model):
    _inherit = 'pos.order'

    nro_tarjeta = fields.Char(string='Número de Tarjeta')

    def _prepare_invoice_vals(self):
        res = super(SdInheritPosOrder, self)._prepare_invoice_vals()
        pago_id = 1
        lista_pagos = list(set(self.payment_ids.mapped('payment_method_id')))
        # print('conjunto pagos',lista_pagos)
        metodo_pago_ids = self.env['metodo.pago.siat'].search([])
        if len(lista_pagos) == 1:
            pago_id = lista_pagos[0].sd_metodo_pago_siat.id
        elif len(lista_pagos) <= 3:

            pagos_pdv =sorted([pago.sd_metodo_pago_siat.name for pago in lista_pagos])
            # print('pagos pv',pagos_pdv)
            for metodo_id in metodo_pago_ids.filtered(lambda x: len(re.split(" – | - ", x.sd_descripcion))==len(lista_pagos)):
                resultado = sorted(re.split(" – | - ", metodo_id.sd_descripcion))
                # print('resultado', resultado)
                if self.es_gift(lista_pagos):
                    pagos_pdv_2 = [item.replace('GIFT-CARD', 'GIFT') for item in pagos_pdv]
                    pagos_pdv_3 = [item.replace('GIFT-CARD', 'GIFT CARD') for item in pagos_pdv]
                    if pagos_pdv == resultado or pagos_pdv_2 == resultado or pagos_pdv_3 == resultado:
                        pago_id = metodo_id.id
                        break
                elif pagos_pdv == resultado:
                    pago_id = metodo_id.id
                    break
        else:
            raise UserError(_('No es posible seleccionar mas de tres metodos de pago.'))
        res['sd_metodo_pago'] = pago_id
        return res

    def es_gift(self, lista_pagos):
        res = False
        for pago in lista_pagos:
            if pago.sd_metodo_pago_siat.name in ('GIFT-CARD', 'GIFT', 'GIFT CARD'):
                res = True
        return res
