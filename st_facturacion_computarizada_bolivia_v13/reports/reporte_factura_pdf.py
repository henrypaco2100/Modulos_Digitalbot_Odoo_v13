from odoo import api, fields, models,_
import time
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import qrcode
import base64
from io import BytesIO

class ihnerit_factura_computarizada_pdf(models.Model):
	_inherit = 'account.move'
	visible = fields.Char()

	def imprimir_factura_computarizada_pdf(self):
		self.validar_campos_necesario_factura()
		pdf = self.env.ref('st_facturacion_computarizada_bolivia_v13.action_report_factura_pdf').render_qweb_pdf(self.ids)
		b64_pdf = base64.b64encode(pdf[0])
		# save pdf as attachment
		name = 'Factura/'+self.fcb_numero_factura_computarizada + '.pdf'
		return self.env['ir.attachment'].create({
			'name': name,
			'type': 'binary',
			'datas': b64_pdf,
			# 'datas_fname': name + '.pdf',
			'store_fname': name,
			'res_model': self._name,
			'res_id': self.id,
			'public': True,
			'mimetype': 'application/pdf'
		})

	def generate_factura_qr(self):
		qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=20, border=4, )
		nit = self.fcb_nit_a_facturar or self.partner_id.vat
		qr.add_data(
			self.env.user.company_id.vat +'|'+str(self.fcb_numero_factura_computarizada)+'|'+self.journal_id.fcb_numero_autorizacion_diario+'|'+
			self.invoice_date.strftime("%d/%m/%Y")+'|'+ str(self.amount_total)+'|'+ str(self.amount_total)+'|'+self.fcb_codigo_de_control+'|'+
			nit+'|'+'0'+'|'+'0'+'|'+'0'+'|'+'0'

		)
		qr.make(fit=True)

		img = qr.make_image()

		buffer = BytesIO()
		img.save(buffer, format="PNG")

		img_str = base64.b64encode(buffer.getvalue())
		print('img_str',img_str)
		return img_str
	def fecha_limite_emision(self):
		return self.journal_id.fcb_fecha_limite_emision.strftime("%d/%m/%Y")
	def copia_original(self):
		estado=['ORIGINAL','COPIA CONTABILIDAD']
		return estado
	def linea_producto(self):
		nuevo_objeto_productos=[]
		self.generate_factura_qr() 	# realizamos la fucion para el qr
		for i in self.invoice_line_ids:
			vals={
				'detalle': i.name,
				'cantidad': int(i.quantity),
				'unidad': i.product_uom_id.name,
				'precio_unitario': round(i.price_unit,2),
				'subtotal': round(i.price_subtotal,2),
			}
			nuevo_objeto_productos.append(vals)
		return nuevo_objeto_productos
	def get_numero_factura(self):
		contador_slash = 0
		for letra in self.name:
			if '/' == letra:
				contador_slash += 1
		contador_slash_dos = 0
		concatenar_numero_secuencia = ''
		contar_cadenacion = 0
		for caracter in self.name:
			if contador_slash_dos == contador_slash:
				if contar_cadenacion <= 4:
					concatenar_numero_secuencia = concatenar_numero_secuencia + caracter
				else:
					break
			elif '/' == caracter:
				contador_slash_dos += 1
		return concatenar_numero_secuencia
	def fecha_a_palabras(self):
		diccionario={
			'01':'enero',
			'02': 'febrero',
			'03': 'marzo',
			'04': 'abril',
			'05': 'mayo',
			'06': 'junio',
			'07': 'julio',
			'08': 'agosto',
			'09': 'septiembre',
			'10': 'octubre',
			'11': 'noviembre',
			'12': 'diciembre',
		}
		if self.journal_id.fcb_ciudad_sucursal:
			ciudad=self.journal_id.fcb_ciudad_sucursal.upper()
		elif self.journal_id.fcb_ciudad_matriz:
			ciudad=self.journal_id.fcb_ciudad_matriz.upper()
		else:
			raise UserError(_('No es posible realizar la Factura, No existe "Ciudad Matriz en el Diario"'))
		if self.invoice_date.strftime("%m") in diccionario:
			return ciudad+", "+self.invoice_date.strftime("%d") +' DE '+ diccionario[self.invoice_date.strftime("%m")].upper()+' DEL '+ self.invoice_date.strftime("%Y")

	def numero_to_letras(self,numero):
		indicador = [("", ""), ("MIL", "MIL"), ("MILLON", "MILLONES"), ("MIL", "MIL"), ("BILLON", "BILLONES")]
		entero = int(numero)
		decimal = int(round((numero - entero) * 100))
		# print 'decimal : ',decimal
		contador = 0
		numero_letras = ""
		while entero > 0:
			a = entero % 1000
			if contador == 0:
				en_letras = self.convierte_cifra(a, 1).strip()
			else:
				en_letras = self.convierte_cifra(a, 0).strip()
			if a == 0:
				numero_letras = en_letras + " " + numero_letras
			elif a == 1:
				if contador in (1, 3):
					numero_letras = indicador[contador][0] + " " + numero_letras
				else:
					numero_letras = en_letras + " " + indicador[contador][0] + " " + numero_letras
			else:
				numero_letras = en_letras + " " + indicador[contador][1] + " " + numero_letras
			numero_letras = numero_letras.strip()
			contador = contador + 1
			entero = int(entero / 1000)
		diccionario_Decimal={0,1,2,3,4,5,6,7,8,9}
		if decimal in diccionario_Decimal:
			numero_letras = numero_letras + " " + '0'+str(decimal) + "/100"
		else:
			numero_letras = numero_letras + " " + str(decimal) + "/100"
		return  numero_letras

	def convierte_cifra(self,numero, sw):
		lista_centana = ["", ("CIEN", "CIENTO"), "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS",
						 "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]
		lista_decena = ["", (
		"DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE"),
						("VEINTE", "VEINTI"), ("TREINTA", "TREINTA Y "), ("CUARENTA", "CUARENTA Y "),
						("CINCUENTA", "CINCUENTA Y "), ("SESENTA", "SESENTA Y "),
						("SETENTA", "SETENTA Y "), ("OCHENTA", "OCHENTA Y "),
						("NOVENTA", "NOVENTA Y ")
						]
		lista_unidad = ["", ("UN", "UNO"), "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"]
		centena = int(numero / 100)
		decena = int((numero - (centena * 100)) / 10)
		unidad = int(numero - (centena * 100 + decena * 10))
		# print "centena: ",centena, "decena: ",decena,'unidad: ',unidad

		texto_centena = ""
		texto_decena = ""
		texto_unidad = ""

		# Validad las centenas
		texto_centena = lista_centana[centena]
		if centena == 1:
			if (decena + unidad) != 0:
				texto_centena = texto_centena[1]
			else:
				texto_centena = texto_centena[0]

		# Valida las decenas
		texto_decena = lista_decena[decena]
		if decena == 1:
			texto_decena = texto_decena[unidad]
		elif decena > 1:
			if unidad != 0:
				texto_decena = texto_decena[1]
			else:
				texto_decena = texto_decena[0]
		# Validar las unidades
		# print "texto_unidad: ",texto_unidad
		if decena != 1:
			texto_unidad = lista_unidad[unidad]
			if unidad == 1:
				texto_unidad = texto_unidad[sw]
		return "%s %s %s" % (texto_centena, texto_decena, texto_unidad)
	def validar_campos_necesario_factura(self):
		if not self.company_id.logo:
			raise UserError(_('EL"Logo" de la compañia es un campo necesario para Imprimir la Factura Computarizada. '))
		if not self.company_id.partner_id.st_nombre_compañia_facturar:
			raise UserError(_('El "Nombre a Facturar" de la compañia es un campo necesario para Imprimir la Factura Computarizada. '))
		if not self.partner_id.vat:
			raise UserError(_('El "NIT" del Cliente es un campo necesario para Imprimir la Factura Computarizada. '))

	def error_no_cuadra_con_el_total(self):
		raise UserError(_('La sumatoria del Subtotal no es igual al Total, comuníquese con su Tecnico.'))
