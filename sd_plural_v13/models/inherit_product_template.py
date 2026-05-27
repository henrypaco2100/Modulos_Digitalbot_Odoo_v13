from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SdInheritProductTemplatePl(models.Model):
    _inherit = "product.template"

    sd_informacion_adicional = fields.Text('Informacion Adicional')
    sd_cuenta_pro = fields.Many2one('account.account',string='Cuenta PRO')
    sd_cuenta_reg = fields.Many2one('account.account', string='Cuenta REG')
    sd_tipo_importe = fields.Selection([
        ('group','Grupo de impuesto'),
        ('fixed','Fijo'),
        ('percent','Porcentaje sobre el precio'),
        ('division','Porcentaje sobre el precio, impuestos incluidos'),
    ],string='Cálculo de impuestos',default='fixed')
    sd_amount_impuesto = fields.Float(string='Importe',digits=(16, 4))
    sd_cuenta_coe = fields.Many2one('account.account', string='Cuenta COE PRO')
    sd_cuenta_coe_reg = fields.Many2one('account.account', string='Cuenta COE REG')

    sd_autor = fields.Char('Autor', readonly=False)

    sd_autor_id = fields.Many2one('res.partner', string='Autor Partner')

    sd_tematica = fields.Char('Temática')
    sd_coleccion = fields.Char('Colección')
    sd_gestion_publicacion = fields.Char('Año Publicación')
    sd_edicion = fields.Selection([('Primera', 'Primera'), ('Segunda', 'Segunda'), ('Tercera', 'Tercera'),
                                   ('Cuarta', 'Cuarta'), ('Quinta', 'Quinta'), ('Sexta', 'Sexta'),
                                   ('Séptima', 'Septima'), ('Octava', 'Octava'), ('Novena', 'Novena'),
                                   ('Décima', 'Decima'), ('Decimoprimera', 'Decimoprimera'),
                                   ('Decimosegunda', 'Decimosegunda'), ('Decimotercera', 'Decimotercera'),
                                   ('Decimocuarta', 'Decimocuarta'), ('Decimoquinta', 'Decimoquinta')],
                                  string='Edición')
    sd_deposito_legal = fields.Char('Deposito Legal')
    sd_observaciones = fields.Text('Observaciones')

    sd_paginas = fields.Integer('Páginas')
    sd_formato = fields.Char('Formato')
    sd_tipo_tapa = fields.Char('Tipo de Tapa')
    sd_precio_FOB_USD = fields.Char('Precio FOB USD')
    sd_tiraje = fields.Char('Tiraje')
    sd_comentarios = fields.Text('Reseña')

    sd_libro_lcv = fields.Boolean('Libro LCV')

    sd_codigo_interno = fields.Char('Código Interno')

    @api.onchange('sd_autor_id')
    def _compute_sd_autor_id(self):
        for record in self:
            record.sd_autor = record.sd_autor_id.name

    def name_get(self):
        result = []
        for product in self:
            components = filter(None, [product.default_code, product.name, product.sd_codigo_interno])
            name = ' '.join(components)
            result.append((product.id, name))
        return result


class SdInheritProductProductoPl(models.Model):
    _inherit = "product.product"

    def name_get(self):
        result = []
        for product in self:
            components = filter(None, [product.default_code, product.name, product.sd_codigo_interno])
            name = ' '.join(components)
            result.append((product.id, name))
        return result