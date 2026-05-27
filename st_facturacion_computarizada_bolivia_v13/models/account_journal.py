from odoo import api, fields, models, _
from suds.client import Client

class ihneritAccountJournal(models.Model):
    _inherit = 'account.journal'
    #DIARIO

    fcb_es_computarizado = fields.Boolean(string="Computarizado", default=False)


    #FACTURA COMPUTARIZADA
    fcb_tipo_factura = fields.Selection([
        ('Internal_Consumption', 'Consumo Interno'),
        ('Export', 'Exportacion'),
        ('Taxed', 'Gravado'), ], string='Tipo de Factura',default='Internal_Consumption')
    fcb_numero_autorizacion_diario = fields.Char(string="Numero de Autorización")
    fcb_llave_de_dosificacion = fields.Char(string="Llave de Dosificación")
    fcb_fecha_activacion = fields.Date(string="Fecha de Activación")
    fcb_fecha_limite_emision = fields.Date(string="Fecha Limite de Emisión")
    fcb_tipo_de_sucursal_factura = fields.Char(string="Tipo de Sucursal")
    fcb_direccion_sucursal_factura = fields.Char(string="Dirección de Sucursal")
    fcb_actividad_economica = fields.Char(string = "Actividad Economica")
    fcb_casa_matriz = fields.Boolean(string="Es Casa Matriz")
    fcb_ciudad_sucursal = fields.Char(string="Ciudad Sucursal")
    fcb_telefono_sucursal = fields.Char(string="Telefono Sucursal")
    fcb_ciudad_matriz = fields.Char(string="Ciudad Matriz")
    fcb_telefono_matriz = fields.Char(string="Telefono Matriz")
    fcb_direccion_matriz = fields.Char(string="Dirección Matriz")
    fcb_type_company = fields.Selection([
            ('uni_personal', 'Unipersonal'),
            ('soc_res_limitada', 'Sociedad de Responsabilidad Limitada'),
            ('soc_anonima', 'Sociedad Anonima'), ],
        string="Tipo de Empresa")
    fcb_siguiente_Numero = fields.Integer(string='Siguiente Nº para la Factura Computarizada', readonly=True,default=1)


    # controlar el numero de caracteres maximo 15 en el campo numero de facturacion
    @api.onchange('fcb_numero_autorizacion_diario')
    def maximo_caracteres(self):

        caracteres=self.fcb_numero_autorizacion_diario
        diccionario_numerico={'0','1','2','3','4','5','6','7','8','9'}
        if caracteres:
            for i in caracteres:
                if not i in diccionario_numerico:
                    self.fcb_numero_autorizacion_diario=''
                    return {
                        'warning': {
                            'message': _(
                                f'Se permiten solo caracteres numérico en el campo: "Fecha de Activación", porfavor vuelva a intentarlo!!. ')
                        }
                    }
            if len(caracteres)>15:
                self.fcb_numero_autorizacion_diario = ''
                return {
                    'warning': {
                        'message': _(
                            f'La cantidad maxima de digitos en el campo "Fecha de Activación" es de "15" , porfavor vuelva a intentarlo!!. ')
                    }
                }

    @api.onchange('type')
    def es_computarizado_control(self):
        if self.type != 'sale':
            self.fcb_es_computarizado= False
    def incrementar_siguiente_numero_factura_computarizada(self):
        numero_siguiente = self.fcb_siguiente_Numero + 1
        if self.fcb_fecha_activacion <= fields.Date.today():
            if fields.Date.today() <= self.fcb_fecha_limite_emision:
                self.write({
                    'fcb_siguiente_Numero':numero_siguiente
                })
    def concatenar_ceros_numero_factura(self,Numero_Factura):
        if len(str(Numero_Factura)) < 5:
            nuevo_numero =str(Numero_Factura)
            cantidad_ceros = 5-len(str(Numero_Factura))
            i=1
            while i <= cantidad_ceros:
                nuevo_numero = '0'+ str(nuevo_numero)
                i = i +1
            return nuevo_numero

        else:
            return str(Numero_Factura)