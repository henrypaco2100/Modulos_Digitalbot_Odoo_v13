from odoo import api, fields, models,SUPERUSER_ID,_
# HEREDAMOS EL METODO ONCHANGE PARA RESTRINGIER LOS TIPO DE OPERACION

class InheritSProductTemplateDecimal(models.Model):
    _inherit = "product.template"

    sd_price_2_decimal = fields.Float('Age', digits=(12,2), default=28.00)

    # def format_price(self):
    #     return round(self.price, 2)



