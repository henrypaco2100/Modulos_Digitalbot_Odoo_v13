from odoo import api, fields, models, tools, _

class InheritAutomatedSale(models.Model):
    _inherit = 'sale.order'

    def action_automate(self):
        vals = super(InheritAutomatedSale, self).action_automate()
        self.date_order_2 = self.date_order
        return vals