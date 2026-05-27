from odoo import models, fields, api, _

class PurchaseOrderLine(models.Model):
    _name = 'sub.category.udm'

    name = fields.Char(string='Nombre')