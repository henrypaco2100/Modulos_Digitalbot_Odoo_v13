from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class SdCompraIvaPlural(models.Model):
    _name = 'compra.iva'
    # electronic.billing
    _check_company_auto = True
    sd_move_id = fields.Many2one('account.move', string='Asiento')
    sd_especificacion = fields.Integer('Esp')
    sd_nro = fields.Integer('Nº')
    sd_fecha_fact = fields.Date('FECHA DE FACTURA/DUI/DIM', required=True, default=lambda self:fields.Date.today())
    partner_id = fields.Many2one('res.partner', string='RAZON SOCIAL PROVEEDOR', required=True)
    sd_nit = fields.Char('NIT PROVEEDOR', required=True ,readonly=False, related='partner_id.vat')
    sd_nro_fact = fields.Char('NUMERO FACTURA', required=True)
    sd_nro_dui = fields.Char('NUMERO DUI/DIM')
    sd_autorizacion = fields.Char('CODIGO DE AUTORIZACION', required=True)
    sd_importe_total = fields.Float('IMPORTE TOTAL COMPRA', required=True)
    sd_importe_nscf = fields.Float('OTRO NO SUJETO A CREDITO FISCAL')
    sd_subtotal = fields.Float('SUBTOTAL',compute='_compute_CF')
    sd_descuentos_iva = fields.Float('DESCUENTOS/BONIFICACIONES/REBAJAS SUJETAS AL IVA')
    sd_importe_base = fields.Float('IMPORTE BASE CF',compute='_compute_CF')
    sd_credito_fiscal = fields.Float('CREDITO FISCAL',compute='_compute_CF')
    sd_codigo_control = fields.Char('CODIGO DE CONTROL')
    sd_tipo = fields.Selection([
        ('1', 'INTERNO / ACTIVIDADES AGRAVADAS'),
        ('2', 'INTERNO / ACTIVIDADES NO AGRAVADAS'),
        ('3', 'SUJETAS A PROPORCIONALIDAD'),
        ('4', 'EXPORTACIONES'),
        ('5', 'INTERNO/EXPORTACIONES'),
    ], string='TIPO COMPRA', required=True)
    sd_origen = fields.Char('Origen')
    sd_importe_ice = fields.Float('IMPORTE ICE')
    sd_importe_iehd = fields.Float('IMPORTE IEHD')
    sd_importe_ipj = fields.Float('IMPORTE IPJ')
    sd_tasas = fields.Float('TASAS')
    sd_importes_exentos = fields.Float('IMPORTES EXENTOS')
    sd_importe_compra_gravada_tasa_cero = fields.Float('IMPORTE COMPRAS GRAVADAS A TASA CERO')
    sd_importe_gift_card = fields.Float('IMPORTE GIFT CARD')
    sd_es_credito_fiscal = fields.Selection([
        ('1', 'SI'),
        ('2', 'NO'),
    ], string='CON DERECHO A CREDITO FISCAL')
    sd_estado_consolidacion = fields.Selection([
        ('1', 'CONSOLIDADO'),
        ('2', 'PENDIENTE'),
    ], string='ESTADO CONSOLIDACION')
    store_id = fields.Many2one(
        'res.store',
        string='Tienda'
    )
    sd_cuf = fields.Char('CUF')
    account_account_id = fields.Many2one('account.account',string='Cuenta')
    account_analytic_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica')

    @api.depends('sd_importe_total', 'sd_importe_nscf', 'sd_descuentos_iva')
    def _compute_CF(self):
        for record in self:
            record.sd_subtotal = record.sd_importe_total - record.sd_importe_nscf
            record.sd_importe_base = record.sd_importe_total - record.sd_importe_nscf -record.sd_descuentos_iva
            record.sd_credito_fiscal =  record.sd_importe_base * 0.13
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """
        Para que usuarios los usuarios no puedan elegir diarios donde no puedan
        escribir, modificamos la funcion search. No lo hacemos por regla de
        permiso ya que si no pueden ver los diarios termina dando errores en
        cualquier lugar que se use un campo related a algo del diario
        """
        user = self.env.user
        # if superadmin, do not apply
        if not self.env.is_superuser():
            args += ['|', ('store_id', '=', False), ('store_id', 'child_of', [user.store_id.id])]
        return super()._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)

