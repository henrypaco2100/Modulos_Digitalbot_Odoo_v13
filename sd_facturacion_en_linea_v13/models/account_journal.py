from odoo import api, fields, models, _
# from suds.client import Client
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class ihneritAccountJournalFacturaElecrtonica(models.Model):
    _inherit = 'account.journal'

    @api.model
    def get_selection_field(self, modelo):
        docs = self.env[modelo].sudo().search([])
        res = []
        for doc in docs:
            res.append((str(doc.sd_codigo_clasificador), str(doc.sd_descripcion)))
        return res

    sd_factura_online_id = fields.Many2one('online.billing.siat', string='factura en linea', copy=False)
    sd_company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                    default=lambda self: self.env.company)
    fcb_es_electronico = fields.Boolean(string="En linea", default=0,readonly=True, copy=False)
    sd_codigo_cuis = fields.Char(string="CUIS",readonly=True, copy=False)
    sd_fecha_vigencia_cuis = fields.Datetime(string='Fecha Vigencia Cuis', readonly=True, copy=False)
    sd_cufd = fields.Char("CUF", help="Codigo unico de Facturacion de Impuesto Nacionales", readonly=True, copy=False)
    sd_fecha_vigencia_cufd = fields.Datetime(related='sd_factura_online_id.sd_fecha_vigencia_cufd',string='Fecha Vigencia Cufd', readonly=True, copy=False)
    sd_nit_em = fields.Char(related='sd_factura_online_id.sd_nit_em')
    sd_razon_social = fields.Char(related='sd_company_id.name')
    sd_municipio = fields.Char(related='sd_factura_online_id.sd_municipio',)
    sd_cufd = fields.Char(related='sd_factura_online_id.sd_cufd', copy=False)
    sd_codigo_sucursal = fields.Selection(related='sd_factura_online_id.sd_codigo_sucursal')
    sd_direccion = fields.Char(related='sd_factura_online_id.sd_direccion', copy=False)
    fcb_siguiente_Numero = fields.Integer(string='Siguiente Nº para la Factura en Linea', readonly=True, default=1, copy=False)
    sd_contador_leyenda = fields.Integer(string='contador', default=1)
    sd_siguiente_leyenda_id = fields.Many2one('leyenda.factura.siat', string='Siguiente Leyenda Factura')
    sd_siguiente_numero_debito_credito = fields.Integer(string='Siguiente Nº para debito-credito en Linea', readonly=True, default=1, copy=False)
    sd_documento_sector_siat = fields.Selection(
        selection=lambda self: self.get_selection_field('tipo.documento.sector.siat'),
        string='Tipo Documento sector', copy=False)

    def siguiente_numero_facturacion(self):
        if self.sd_factura_online_id.existe_cuis():
            numero_siguiente = self.fcb_siguiente_Numero + 1
            self.write({
                'fcb_siguiente_Numero': numero_siguiente
            })

    def siguiente_numero_debito_credito(self):
        if self.sd_factura_online_id.existe_cuis():
            numero_siguiente = self.sd_siguiente_numero_debito_credito + 1
            self.write({
                'sd_siguiente_numero_debito_credito': numero_siguiente
            })
    # def solicitar_cuis_sin(self):
    #     # try:
    #     wsdl = "https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionCodigos?wsdl"
    #     cliente = Client(wsdl)
    #     print(cliente)
        # session = Session()
        # session.auth = HTTPBasicAuth("Diego2012", "Diego2012")
        # client = Client(wsdl=wsdl, transport=Transport(session=session))
        # codigoAmbiente = self.sd_codigo_ambiente
        # requests_data = {"codigoAmbiente": self.sd_codigo_ambiente,
        #                  "codigoModalidad": self.sd_codigo_modalidad,
        #                  "codigoSistema": self.sd_codigo_sistema,
        #                  "nit": self.sd_nit_em,
        #                  "datosSolicitud": '00',
        #                  "codigoSucursal": self.sd_codigo_sucursal},

        # request_data = {'codigoAmbiente': codigoAmbiente,
        #                 'codigoModalidad': ,
        #                 'codigoSistema': ,
        #                 'nit': ,
        #                 'datosSolicitud': ,
        #                 'codigoSucursal': ,
        #                 },
        # response = client.service.cuisMasivo(codigoAmbiente=self.sd_codigo_ambiente,
        #                                      codigoModalidad=self.sd_codigo_modalidad,
        #                                      codigoSistema=self.sd_codigo_sistema,
        #                                      nit=self.sd_nit_em,
        #                                      datosSolicitud="00",
        #                                      codigoSucursal=self.sd_codigo_sucursal)
        # result = client.service['cuisMasivo']()
        # response = client.service.verificarNit()
        # self.cuis = response['cuisMasivoResponse']

        # except Fault as fault:
        #     parsed_fault_detail = client.wsdl.types.deserialize(fault.detail[0])

    # def solicitar_cufd_sin(self):
    #     wsdl = "https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionCodigos?wsdl"
        # client = Client(wsdl)
        # session = Session()
        # session.auth = HTTPBasicAuth("Diego2012", "Diego2012")
        # client = Client(wsdl, transport=Transport(session=session))
        # client.service['cuisMasivo']()
        # client.service("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJkaWVnbzIwMTIiLCJjb2RpZ29TaXN0ZW1hIjoiNkQwQTYzMTAyREQzNzFCNDJENDMwRkUiLCJuaXQiOiJINHNJQUFBQUFBQUFBTE13TURBME56STNNRFFBQUpaWnkxWUtBQUFBIiwiaWQiOjE1OTAyNywiZXhwIjoxNjM1NjM4NDAwLCJpYXQiOjE2MzMxMDk0MTIsIm5pdERlbGVnYWRvIjo4MDAxNzI3MDEwLCJzdWJzaXN0ZW1hIjoiU0ZFIn0.0CCRfT28ssFsSOwlH7Lr3kNasL73aWLfgak1KEGNPS6mVVPLPBgdWvYNJTR48vVMl4kbk8NByoVpwVctxeusPQ")