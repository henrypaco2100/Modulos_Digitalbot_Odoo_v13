from odoo import api, fields, models, _

class SdInheritPosConfig(models.Model):
    _inherit = 'pos.config'

    sd_fcb_es_electronico = fields.Boolean('en linea', related="invoice_journal_id.fcb_es_electronico")
    sd_download_pdf = fields.Boolean('Descargar Pdf')
