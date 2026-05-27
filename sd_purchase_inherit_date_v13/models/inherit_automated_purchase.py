from odoo import api, fields, models, tools, _

class InheritAutomatedPurchase(models.Model):
    _inherit = 'purchase.order'

    def action_automate(self):
        vals = super(InheritAutomatedPurchase, self).action_automate()
        self.date_order_2 = self.date_order
        return vals