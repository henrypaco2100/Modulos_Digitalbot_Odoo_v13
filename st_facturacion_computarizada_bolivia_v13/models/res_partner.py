from odoo import api, fields, models, _

class inherit_Contacto(models.Model):
    _inherit = 'res.partner'

    vat = fields.Char(required=True)
    st_nombre_compañia_facturar = fields.Char(string='Nombre a Facturar', required=True)

    @api.onchange('vat')
    def maximo_caracteres(self):
        caracteres=self.vat
        diccionario_numerico={'0','1','2','3','4','5','6','7','8','9'}
        if caracteres:
            for i in caracteres:
                if not i in diccionario_numerico:
                    self.vat=''
                    return {
                        'warning': {
                            'message': _(
                                f'Se permiten solo caracteres numérico en el campo: "NIF", porfavor vuelva a intentarlo!!. ')
                        }
                    }
            if len(caracteres) > 12:
                self.vat = ''
                return {
                    'warning': {
                        'message': _(
                            f'La cantidad maxima de digitos en el campo "NIF" es de "12", porfavor vuelva a intentarlo!!. ')
                    }
                }

