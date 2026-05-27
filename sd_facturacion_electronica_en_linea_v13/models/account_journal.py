from odoo import api, fields, models, _
from suds.client import Client
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class ihneritAccountJournalFacturaElecrtonica(models.Model):
    _inherit = 'account.journal'
    fcb_es_electronico = fields.Boolean(string="Electronica", default=0,readonly=True)
    sd_codigo_cuis = fields.Char(string="CUIS",readonly=True)
    sd_fecha_vigencia_cuis = fields.Datetime(string='Fecha Vigencia Cuis', readonly=True)
    sd_cufd = fields.Char("CUF", help="Codigo unico de Facturacion de Impuesto Nacionales", readonly=True)
    sd_fecha_vigencia_cufd = fields.Datetime(string='Fecha Vigencia Cufd', readonly=True)

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