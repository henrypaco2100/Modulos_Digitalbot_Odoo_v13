from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
class SdInheritSaleOrderSiat(models.Model):
    _inherit = 'sale.order'

    @api.model
    def get_selection_field(self, modelo):
        docs = self.env[modelo].sudo().search([])
        res = []
        for doc in docs:
            res.append((str(doc.sd_codigo_clasificador), str(doc.sd_descripcion)))
        return res

    @api.model
    def _get_default_metodo_pago(self):
        metodo_efectivo = self.env['ir.model.data'].xmlid_to_res_id(
            "sd_facturacion_en_linea_v13.sd_data_metodo_pago_default")
        # print(metodo_efectivo, 'metodo efectivo')
        return metodo_efectivo

    sd_razon_social = fields.Char(related='partner_id.st_nombre_compania_facturar', readonly=False)
    sd_nro_documento = fields.Char(related='partner_id.vat', readonly=False)
    sd_codigo_tipo_documento = fields.Selection(related='partner_id.sd_codigo_tipo_documento', readonly=False)
    sd_email = fields.Char(related='partner_id.email', readonly=False)
    sd_nombre_facturado = fields.Char('Nombre Facturado', copy=False)
    sd_email_facturado = fields.Char('Email Facturado', copy=False)
    sd_tipo_documento_facturado = fields.Selection(
        selection=lambda self: self.get_selection_field('documento.identidad.siat'), string='Tipo Documento Facturado',
        copy=False)
    sd_nro_documento_facturado = fields.Char('NIT/CI/CEX Facturado', copy=False)
    sd_extension = fields.Char('Complemento Facturado', copy=False)
    sd_metodo_pago = fields.Many2one('metodo.pago.siat', string='Método Pago',
                                     default=lambda self: self._get_default_metodo_pago(),
                                     domain="[('sd_activo','=',True)]")