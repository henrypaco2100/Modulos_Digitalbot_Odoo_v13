from odoo import api, fields, models, _

class ihneritAccountJournal(models.Model):
    _inherit = 'facturacion.computarizada.bolivia'
    prueba_numero_autorizacion= fields.Char(string="Nº Autorizacion")
    prueba_numero_factura= fields.Char(string="Nº Factura")
    prueba_Nit_cliente= fields.Char(string='Nit/Cl Comprador')
    prueba_fecha_emision= fields.Date(string="Fecha emision")
    prueba_monto=fields.Monetary(string='Monto en bs',currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    prueba_llave_dosificacion= fields.Char(string="Llave Dosificacion")
    prueba_codigo_control=fields.Char(string="Codigo de Control", readonly=True)
    prueba_Verhoeff= fields.Char(string='Verhoeff')
    prueba_digitos_generados = fields.Char(string='Digitos generados Verhoeff')
    prueba_generar_subcadena = fields.Char(string='Subcadena')
    prueba_pase_3_AllegedRC4 = fields.Char(string='Generado por AllegedRC4')
    prueba_sumatoria_ascii = fields.Char(string='Sumatoria')
    prueba_base_64 = fields.Char(string='Base 64')


    def generar_codigo_control_prueba(self):
        # monto_prueba= int(self.prueba_monto)
        prueba_codigo_control= self.generar_codigo_control(self.prueba_fecha_emision,
                                            self.prueba_numero_factura,
                                            self.prueba_Nit_cliente,
                                            self.prueba_numero_autorizacion,
                                            self.prueba_llave_dosificacion,self.prueba_monto)
        self.write({'prueba_codigo_control': prueba_codigo_control})

## funciones Auxiliares para testear
    def generar_Verhoeff_prueba(self):

        prueba_codigo_control = self.adddigitosVerhoreff(int(self.prueba_numero_autorizacion),5)
        prueba_digitos_generados = self.obtener_los_ultimos_digitos(prueba_codigo_control,5)
        self.write({
            'prueba_Verhoeff': prueba_codigo_control,
            'prueba_digitos_generados':prueba_digitos_generados,
        })
    def generar_Subcadena(self):
        digito= self.prueba_numero_autorizacion
        prueba_generar_subcadena= self.concatenar_datos_factura_cadena(digito[4],
                                                                       self.prueba_numero_factura,
                                                                       self.prueba_llave_dosificacion)
        self.write({
            'prueba_generar_subcadena': prueba_generar_subcadena,
            'prueba_llave_dosificacion': self.Subcadena_llave

        })
    def generar_con_AllegedRC4_paso3(self):
        prueba_pase_3_AllegedRC4 = self.aplicar_allegedRC4_sin_guion(self.prueba_numero_autorizacion,self.prueba_llave_dosificacion)
        self.write({
            'prueba_pase_3_AllegedRC4': prueba_pase_3_AllegedRC4

        })
    def generar_sumatoria_ASCII_paso_4(self):
        prueba_sumatoria_ascii = self.sumatoria_ASCII(self.prueba_pase_3_AllegedRC4)
        self.write({
            'prueba_sumatoria_ascii': prueba_sumatoria_ascii,

        })
    def generar_base_64_paso5(self):
        lista= self.prueba_sumatoria_ascii
        lista = lista[1:-1]
        lista= lista.split(sep=", ")
        prueba_base_64 = self.multilplicar_and_sumar_paso5(lista,self.prueba_numero_autorizacion)
        self.write({
            'prueba_base_64': prueba_base_64,

        })