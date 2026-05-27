from selenium import webdriver
from datetime import date,datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
# import sched
# import time


class InheritAgenciaDespachante(models.Model):
    _inherit = 'despacho.importacion'
    def init_chrome(self):
        # iniciar chromedirver
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        self.browser = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver',options=chrome_options)

    def init_sesion_click(self,gestion,aduana_destino,numero_DIM):
        # iniciar sesion
        self.browser.get('http://anbsw01.aduana.gob.bo:7601/click/')
        self.browser.find_element_by_id('gestion').send_keys(gestion)
        self.browser.find_element_by_id('aduana').send_keys(aduana_destino)
        self.browser.find_element_by_name('serie').send_keys('C')
        self.browser.find_element_by_id('numero').send_keys(numero_DIM)
        self.browser.implicitly_wait(5)
        self.browser.find_element_by_id('consulta').click()

        # Validacion de Inicio de Sesion
        entro_a_la_web = self.browser.find_element_by_xpath('/html/body/div[2]/table/tbody/tr[1]/th').text
        print("verificar",entro_a_la_web)
        if entro_a_la_web != 'Régimen aduanero':
            raise UserError('los Datos ingresados son incorrectos.')

    def scraping_aduana_nacional(self):
        # Verificar el Dia
        dia_existe = self.verificar_dia(self.browser)
        mensaje=''
        if not dia_existe == 0:
            if dia_existe == 1:
                mensaje = self.browser.find_element_by_xpath('/html/body/div[2]/div[2]/table/tbody/tr[1]/td[2]').text
            elif dia_existe == 2:
                mensaje = self.browser.find_element_by_xpath('/html/body/div[2]/div[2]/table/tbody/tr[2]/td[4]').text
            #     /html/body/div[2]/div[2]/table/tbody/tr[2]/td[3]
            elif dia_existe == 3:
                mensaje = self.browser.find_element_by_xpath('/html/body/div[2]/div[2]/table/tbody/tr[3]/td[2]').text
            elif dia_existe == 4:
                mensaje = self.browser.find_element_by_xpath('/html/body/div[2]/div[2]/table/tbody/tr[4]/td[1]').text
            elif dia_existe == 5:
                mensaje = self.browser.find_element_by_xpath('/html/body/div[2]/div[2]/table/tbody/tr[5]/td[2]').text

            self.browser.implicitly_wait(5)
        self.browser.find_element_by_xpath('/html/body/div[2]/div[1]/form/input').click()
        #browser.quit()
        return mensaje
    def verificar_dia(self,browser):
        fecha_lunes = browser.find_element_by_xpath('/html/body/div[2]/div[2]/table/tbody/tr[1]/th[1]/b').text
        fecha_martes = browser.find_element_by_xpath('/html/body/div[2]/div[2]/table/tbody/tr[2]/th[1]/b').text
        # /html/body/div[2]/div[2]/table/tbody/tr[2]/td[4]/text()[2]
        # fecha_miercoles = browser.find_element_by_xpath('/html/body/div[2]/div[2]/table/tbody/tr[3]/th[1]/b').text
        # fecha_jueves = browser.find_element_by_xpath('/html/body/div[2]/div[2]/table/tbody/tr[4]/th[1]/b').text
        # fecha_viernes = browser.find_element_by_xpath('/html/body/div[2]/div[2]/table/tbody/tr[5]/th[1]/b').text

        print('fecha hoy',datetime.datetime.now())
        fecha_actual = (datetime.datetime.now() - datetime.timedelta(hours=4)).date()
        fecha_actual = fecha_actual.strftime("%d/%m/%Y")
        print(fecha_lunes, fecha_actual)
        numero_dia = 0
        if 'lunes '+fecha_actual == fecha_lunes:
            numero_dia = 1
        elif 'martes '+fecha_actual == fecha_martes:
            numero_dia = 2
        # elif 'miércoles '+fecha_actual == fecha_miercoles:
        #     numero_dia = 3
        # elif 'jueves '+fecha_actual == fecha_jueves:
        #     numero_dia = 4
        # elif 'viernes '+'26/02/2021' == fecha_viernes:
        #     numero_dia = 5

        # prueba demo
        numero_dia=2
        return numero_dia
    def _ultimo_mensaje(self,mensaje,despacho):
        print("despacho",despacho,mensaje)
        if mensaje != '':
            if despacho.st_ultimo_mensaje != mensaje:

                despacho.write({
                    'st_ultimo_mensaje':mensaje,
                })
                despacho.create_new_line_follow()
                odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
                print("odoo bot id")
                despacho.sudo().message_post(body=mensaje, author_id=odoobot_id, message_type="comment",subtype="mail.mt_comment")

    def finalizar_chromedriver(self):
        self.browser.quit()
    def funcion_principal_despacho(self):
        self.init_chrome()
        objetos_despachos= self.env['despacho.importacion'].search([('state','=','opened')])
        if objetos_despachos:
            for despacho in objetos_despachos:
                gestion = despacho.st_fecha_declaracion.strftime("%Y")
                print(gestion,despacho.st_aduana_destino,despacho.st_numero_dim)
                self.init_sesion_click(gestion,despacho.st_aduana_destino,despacho.st_numero_dim)
                mensaje= self.scraping_aduana_nacional()
                self._ultimo_mensaje(mensaje,despacho)
        self.finalizar_chromedriver()

