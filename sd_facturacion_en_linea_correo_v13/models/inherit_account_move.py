from odoo import api, fields, models, _
import base64
from datetime import datetime, timedelta
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
class SdInheritAccountMoveCorreoSiat(models.Model):
    _inherit = 'account.move'

    @api.depends('sd_sucursal')
    def actualizar_sucursal(self):

        for move in self:
            move.sd_sucursal_str  = ''

            valor_seleccionado = move.obtener_sucursal_report()
            move.update({
                'sd_sucursal_str': str(valor_seleccionado),
            })


    sd_is_facturacion_linea = fields.Boolean('es facturacion en linea', related='journal_id.fcb_es_electronico')
    # sd_nro_factura_siat = fields.Integer('No. Factura')
    # ---------------campos factura para pos------------------------
    sd_tipo_factura = fields.Selection('tipo factura', related='journal_id.sd_factura_online_id.sd_tipo_factura')
    sd_nombre_company = fields.Char('Razon social', related='journal_id.sd_factura_online_id.sd_nombre_company')
    sd_sucursal = fields.Selection('Sucursal', related='journal_id.sd_factura_online_id.sd_codigo_sucursal')
    sd_sucursal_str = fields.Char('sucursal str', store=False, compute="actualizar_sucursal")
    sd_nro_pv = fields.Integer('nro pv', related='journal_id.sd_factura_online_id.sd_codigo_punto_venta.sd_codigo_punto_venta')
    sd_direccion = fields.Char('direccion', related='journal_id.sd_direccion')
    sd_nro_company = fields.Char('telefono compañia', related='journal_id.sd_factura_online_id.sd_nro_company')
    sd_municipio = fields.Char('municipio', related='journal_id.sd_factura_online_id.sd_municipio')
    sd_nit_emisor = fields.Char('nit emisor', related='journal_id.sd_factura_online_id.sd_nit_em')
    sd_tipo_emision = fields.Selection('tipo emision', related='journal_id.sd_factura_online_id.sd_tipo_emision')
    def action_imprimir_factura_enviar_correo_siat(self,facturaXml=None,es_pos=None):
        # print('envio correo')
        adjuntos = []
        name = self.name + '.pdf'
        mensaje = 'Facturacion en linea'
        author_id = self.company_id.partner_id
        pdf = self.journal_id.sd_factura_online_id.sd_pantilla_pdf_id.render_qweb_pdf(self.ids)
        b64_pdf = base64.b64encode(pdf[0])
        pdf = self.env['ir.attachment'].sudo().create({
            'name': name,
            'type': 'binary',
            'datas': b64_pdf,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'public': True,
            'mimetype': 'application/pdf'
        })
        adjuntos.append(pdf)
        if facturaXml:
            b64_xml = base64.b64encode(facturaXml)
            xml = self.env['ir.attachment'].sudo().create({
                'name': self.name + '.xml',
                'type': 'binary',
                'datas': b64_xml,
                'store_fname': self.name + '.xml',
                'res_model': self._name,
                'res_id': self.id,
                'public': True,
                # 'mimetype': 'application/pdf'
            })
            # if self.sd_is_offline:
            adjuntos.append(xml)
        # Mensaje Despacho hoja de trabajo
        if self.partner_id.email and self.journal_id.sd_factura_online_id.sd_es_enviar_correo:
            print('antes del if smtp user')
            if self.journal_id.sd_factura_online_id.sd_servidor_correo.smtp_user:
                if es_pos:
                    self.create_mail_message_mail(mensaje, self.partner_id,author_id,adjuntos)


    def action_imprimir_factura_enviar_correo_siat_sudo(self):
        print('se llamo a mi correo')
        xml = self.access_attachments()
        self.sudo().action_imprimir_factura_enviar_correo_siat(facturaXml=xml, es_pos=True)

    def create_mail_message_mail(self,Mensaje,cliente_id,author_id,adjuntos, subject = None):
        # servidor_mail_id = self.env['ir.model.data'].xmlid_to_res_id('sd_facturacion_en_linea_correo_v13.sd_ir_server_mail_facturacion_siat')
        servidor_mail_id = self.journal_id.sd_factura_online_id.sd_servidor_correo
        if servidor_mail_id:
            print('antes de smtpuser')
            email_from = '"'+author_id.name + '"' +' <'+ servidor_mail_id.smtp_user+'>'
            print('email_from',email_from)
            email_reply = self.journal_id.sd_factura_online_id.sd_correo_respuesta
            values = {
                'subject': subject or 'Facturacion en linea ' + self.name,
                'email_from': email_from,
                'reply_to': email_reply,
                'recipient_ids': [cliente_id.id],
                'notification': True,
                'message_type': 'comment',
                'mail_server_id': servidor_mail_id.id,
                'model': self._name,
                'record_name': self.name,
                'display_name':self.name,
                'res_id':self.id,
                'body_html': Mensaje,
                'body':Mensaje,
                'attachment_ids':[adjunto.id for adjunto in adjuntos],
            }
            res_correo = self.env['mail.mail'].sudo().create(values).send()
            print(res_correo)

    def mensaje_personalizador(self, mensaje):
        message_id = self.env['sd.message.wizard'].create({'message': mensaje})
        return {
            'name': 'Proceso Exitoso!!',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sd.message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }

    def anular_factura(self, es_masiva=None):
        """Enviar correo al anaular factura """
        res = super(SdInheritAccountMoveCorreoSiat, self).anular_factura(es_masiva=es_masiva)
        if self.sd_cuf and not self.journal_id.sd_factura_online_id.sd_es_test:
            # print('print correo')
            fecha_backend = self.sd_fecha_emision - timedelta(hours=4)
            fecha_emision = fecha_backend.strftime('%d/%m/%Y %I:%M')
            fecha_emision = fecha_emision + self.obtener_meridem(fecha_backend)
            website = self.company_id.website or ''
            Header = '<p style="text-align: center;">' \
                      '<a href="'+ website +'" class="btn btn-secondary">' \
                        '<img class="img-fluid o_we_custom_image" src="'+ website +'logo.png?access_token=96fd4ff8-5706-4693-91db-c2531cb8b397" style="height: auto; max-width: 100%; vertical-align: middle; width: auto;">' \
                      '</a>' \
                      '<br>' \
                  '</p>'
            mensaje = Header +'<p style="text-align: left;">' \
                             '<font style="color:rgb(0, 49, 99);font-size: 14px;">' \
                                'Estimado/a' \
                             '</font>' \
                             '<font style="color:rgb(0, 0, 0);font-size: 14px;">' \
                             ' </font>' \
                             '<font style="color:rgb(0, 49, 99);font-size: 14px;">' \
                                 '<b>' \
                                    + self.sd_nombre_facturado+'<br/>Nit: '+self.sd_nro_documento_facturado+\
                                 '</b> ' \
                                    '<br/>Su factura <b>Nro:'+ str(self.sd_nro_factura_siat) +'</b>'+'<br/>Cód. Autorización: '+self.sd_cuf+ '<br/>Descripcion: '+ self.sd_codigo_descripcion+'<br/>Fecha Emisión: '+fecha_emision+ \
                             '</font>' \
                          '</p>'
            adjuntos = []
            subject ='Anulacion Factura Nro ' + str(self.sd_nro_factura_siat)
            self.create_mail_message_mail(mensaje,self.partner_id,self.company_id.partner_id,adjuntos,subject =subject)
            return res
    def validar_estado_es_factura_linea(self):
        """validar si es en linea al imprimir pdf"""
        if not self.state == 'posted':
            raise UserError(_("El documento debe de estar publicado."))
        return 'hello'

    # ----------------------validacion para factura online --------------------------
    def verificar_obligatorio(self, diario,cliente):
        vals = super(SdInheritAccountMoveCorreoSiat, self).verificar_obligatorio(diario,cliente)
        if self.journal_id.fcb_es_electronico:
            if not self.journal_id.sd_factura_online_id.sd_pantilla_pdf_id:
                raise UserError(_('Por favor seleccione una plantilla en su factura en linea para continuar. \n En caso de que continue el problema consulte a su soporte.'))
        return vals


    def access_attachments(self):
        for record in self:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', record.id),
                ('name', 'like', '%.xml')
            ])

            if attachments:
                return attachments.datas

    def some_other_method(self):
        # Llamar a la función access_attachments
        self.access_attachments()