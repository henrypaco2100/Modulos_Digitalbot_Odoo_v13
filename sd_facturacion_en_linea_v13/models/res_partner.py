from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class inherit_Contacto(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_selection_field(self):
        docs = self.env['documento.identidad.siat'].sudo().search([])
        res = []
        for doc in docs:
            res.append((str(doc.sd_codigo_clasificador), str(doc.sd_descripcion)))
        return res
    vat = fields.Char(string='NIT/CI/CEX', default=0)
    # st_nombre_compañia_facturar = fields.Char(string='Nombre a Facturar', store=True, company_dependent=True)
    st_nombre_compania_facturar = fields.Char(string='Nombre a Facturar', store=True, company_dependent=True)
    sd_codigo_tipo_documento = fields.Selection(selection=lambda self: self.get_selection_field(),
                                                string='Tipo de documento', store=True, company_dependent=True
                                                )
    sd_prueba_selection = fields.Selection([('1','Option 1'), ('2','Option 2')], string='prueba', store=True, company_dependent=True)
    # sd_nro_documento = fields.Char(string='Numero de documento')
    sd_extension = fields.Char(string='Complemento', store=True, company_dependent=True)
    sd_es_caso_especial = fields.Boolean(string='Especial', default=False, company_dependent=True)
    sd_nro_tarjeta = fields.Char(string='N° Tarjeta', store=True, size=9, company_dependent=True)

    @api.constrains('sd_nro_tarjeta')
    def _check_digits(self):
        for record in self:
            if record.sd_nro_tarjeta and not record.sd_nro_tarjeta.isdigit():
                raise ValidationError("El campo debe contener solo dígitos numéricos.")

    @api.onchange('sd_nro_tarjeta')
    def _onchange_my_field(self):
        for record in self:
            if record.sd_nro_tarjeta and record.sd_nro_tarjeta.isdigit():
                formatted_value = record.sd_nro_tarjeta[:4] + '0' * 8 + record.sd_nro_tarjeta[-4:]
                record.sd_nro_tarjeta = formatted_value

    # selection_field = fields.Selection(
    #     selection=lambda self: self.env['hr.selections'].get_selection_field('selection_name'))
    # @api.onchange('vat')
    # def maximo_caracteres(self):
    #     caracteres=self.vat
    #     diccionario_numerico={'0','1','2','3','4','5','6','7','8','9'}
    #     if caracteres:
    #         for i in caracteres:
    #             if not i in diccionario_numerico:
    #                 self.vat=''
    #                 return {
    #                     'warning': {
    #                         'message': _(
    #                             f'Se permiten solo caracteres numérico en el campo: "NIF", porfavor vuelva a intentarlo!!. ')
    #                     }
    #                 }
    #         if len(caracteres) > 12:
    #             self.vat = ''
    #             return {
    #                 'warning': {
    #                     'message': _(
    #                         f'La cantidad maxima de digitos en el campo "NIF" es de "12", porfavor vuelva a intentarlo!!. ')
    #                 }
    #             }


class inherit_divisas(models.Model):
    _inherit = 'res.currency'

    sd_tipo_moneda = fields.Many2one('tipo.moneda.siat', string='Tipo moneda siat')

