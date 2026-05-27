from odoo import api, fields, models, _

class ihneritPuchaseOrder(models.Model):
    _inherit = 'purchase.order'
    fcb_autorizacion_compra_order = fields.Char(string="Numero de Autorizacion")
    fcb_codigo_control_compra_order = fields.Char(string="Codigo de Control")
    fcb_numero_dim_order = fields.Char(string="Numero de Declaracion de Importacion")
    fcb_tipo_compra_order = fields.Selection([
        ('compra_interno_gravadas', 'Compras para mercado interno con destino a actividades gravadas'),
        ('compra_interno_no_gravadas', 'Compras para mercado interno con destino a actividades no gravadas,'),
        ('compra_proporcionalidad', 'Compras sujetas a proporcionalidad'),
        ('compra_exportaciones', 'Compras para exportaciones'),
        ('compra_interno_exportaciones', 'Compras tanto para el mercado interno como para exportaciones'),
        ],
        string='Factura de Compras')

    @api.onchange('fcb_autorizacion_compra_order')
    def maximo_caracteres(self):

        caracteres = self.fcb_autorizacion_compra_order
        diccionario_numerico = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
        if caracteres:
            for i in caracteres:
                if not i in diccionario_numerico:
                    self.fcb_autorizacion_compra_order = ''
                    return {
                        'warning': {
                            'message': _(
                                f'Se permiten solo caracteres numérico en el campo: "Fecha de Activación", porfavor vuelva a intentarlo!!. ')
                        }
                    }