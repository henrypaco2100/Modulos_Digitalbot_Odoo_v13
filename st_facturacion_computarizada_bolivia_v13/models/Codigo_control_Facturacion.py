from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class FacturacionBolivia(models.Model):
    _name = 'facturacion.computarizada.bolivia'
    _description = 'factura computarizada para Bolivia'

    verhoeff_table_d = (
        (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
        (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
        (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
        (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
        (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
        (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
        (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
        (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
        (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
        (9, 8, 7, 6, 5, 4, 3, 2, 1, 0))
    verhoeff_table_p = (
        (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
        (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
        (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
        (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
        (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
        (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
        (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
        (7, 0, 4, 6, 9, 1, 3, 2, 5, 8))
    verhoeff_table_inv = (0, 4, 3, 2, 1, 5, 6, 7, 8, 9)
    Subcadena_llave = ''

    def obtener_numero_de_secuencia(self, name_secuencia):
        contador_slash = 0
        for letra in name_secuencia:
            if '/' == letra:
                contador_slash += 1
        contador_slash_dos = 0
        concatenar_numero_secuencia = ''
        contar_cadenacion = 0
        for caracter in name_secuencia:
            if contador_slash_dos == contador_slash:
                if contar_cadenacion <= 4:
                    concatenar_numero_secuencia = concatenar_numero_secuencia + caracter
                else:
                    break
            elif '/' == caracter:
                contador_slash_dos += 1
        return int(concatenar_numero_secuencia)
    def generar_codigo_control(self, invoice_date,numerofactura, nit,numero_autorizacion,llave_dosi,amount_total):

        # PASO 0 VALIDACION Y CONTROL DE DATOS INPUT
        #   fecha trasformar entero
        fechafactura = int(invoice_date.strftime("%Y%m%d"))
        # numero factura a entero
        NumerofacturaEntero= int(numerofactura)
        # NIT factura convertir a entero
        nit_factura= nit
        if not nit_factura:
            raise UserError(_("El NIT del usuario no existe!!, no es posible realizar la Factura"))
        nit_factura=int(nit_factura)
        # NUmero de autorizacion convertir a entero
        numero_de_autorizacion =int(numero_autorizacion)

        # Monto total  redondear
        monto_total= int(round(amount_total))

        # llave de dosificacion
        llave_de_dosificacion= llave_dosi

        # PASO 1
        # Agregar el digito verificador Verhoeff.

        Numero_de_Factura_paso2 = self.adddigitosVerhoreff(NumerofacturaEntero,2)
        NIT_del_Cliente_paso2 = self.adddigitosVerhoreff(nit_factura,2)
        Fecha_Transaccion_paso2 = self.adddigitosVerhoreff(fechafactura,2)
        Monto_Total_paso2 = self.adddigitosVerhoreff(monto_total,2)
        # 1.1 Suma Arimetica
        suma_arimetica= int(Numero_de_Factura_paso2)+int(NIT_del_Cliente_paso2)+int(Fecha_Transaccion_paso2)+int(Monto_Total_paso2)
        # 1.2 generar a la Suma Arimetica 5 dígitos Verhoeff

        suma_digitos_5 = self.adddigitosVerhoreff(suma_arimetica,5)
        digitos_5_verhoeff= self.obtener_los_ultimos_digitos(suma_digitos_5,5)
        digitos_5_verhoeff =str(digitos_5_verhoeff)

        # PASO 2
        self.Subcadena_llave = llave_de_dosificacion
        # Numero de autorizacion

        numero_de_autorizacion = self.concatenar_datos_factura_cadena(digitos_5_verhoeff[0],numero_de_autorizacion,self.Subcadena_llave)

        # Numero de factura
        Numero_de_Factura_paso2 = self.concatenar_datos_factura_cadena(digitos_5_verhoeff[1],Numero_de_Factura_paso2,self.Subcadena_llave)

        # NIt del Cliente
        NIT_del_Cliente_paso2 = self.concatenar_datos_factura_cadena(digitos_5_verhoeff[2], NIT_del_Cliente_paso2,self.Subcadena_llave)

        # Fecha_Transaccion
        Fecha_Transaccion_paso2 = self.concatenar_datos_factura_cadena(digitos_5_verhoeff[3], Fecha_Transaccion_paso2,self.Subcadena_llave)

        # Monto_Total
        Monto_Total_paso2 = self.concatenar_datos_factura_cadena(digitos_5_verhoeff[4], Monto_Total_paso2,self.Subcadena_llave)

        # Paso 3
        cadena_concatenada = str(numero_de_autorizacion)+str(Numero_de_Factura_paso2)+str(NIT_del_Cliente_paso2)+str(Fecha_Transaccion_paso2)+str(Monto_Total_paso2)
        cadena_key =str(llave_de_dosificacion)+str(digitos_5_verhoeff)
        resultado_paso_3 = self.aplicar_allegedRC4_sin_guion(cadena_concatenada,cadena_key)

        # PASO 4
        array_resultado = self.sumatoria_ASCII(resultado_paso_3)
        #PASO 5

        caracter_base64 = self.multilplicar_and_sumar_paso5(array_resultado,digitos_5_verhoeff)

        # # PASO 6
        # # codigo de control
        key_final_Concatenada = str(llave_de_dosificacion) +str(digitos_5_verhoeff)


        return self.encryptMessageRC4(caracter_base64,key_final_Concatenada)

    # FUNCIONES AUXILIARES
    # Verhoeff

    def calcsum(self,number):
        """Para un número dado, devuelve un dígito de suma de verificación de Verhoeff"""
        c = 0
        for i, item in enumerate(reversed(str(number))):
            c = self.verhoeff_table_d[c][self.verhoeff_table_p[(i + 1) % 8][int(item)]]
        return self.verhoeff_table_inv[c]

    def checksum(self,number):
        """Para un número dado genera un dígito de Verhoeff y
        devuelve número + dígito"""
        c = 0
        for i, item in enumerate(reversed(str(number))):
            c = self.verhoeff_table_d[c][self.verhoeff_table_p[i % 8][int(item)]]
        return c

    def generateVerhoeff(self,number):
        """Para un número dado devuelve número + dígito de checksum de Verhoeff"""
        return "%s%s" % (number, self.calcsum(number))

    def validateVerhoeff(self,number):
        """Validar número de checksummedn de Verhoeff (la suma de comprobación es el último dígito)"""
        return self.checksum(number) == 0
    def adddigitosVerhoreff(self,number,digitos):
        while digitos > 0:
            number = self.generateVerhoeff(number)
            digitos= digitos-1
        return  number

    # obtener ultimos digitos
    def obtener_los_ultimos_digitos(self, number,digito):
        subcadena = str(number)
        subcadena = subcadena[-digito:]
        return subcadena

    def paso_dos_concatenar(self,llave_dosificacion, digitos):
        digitos=int(digitos)+1
        subcadena = llave_dosificacion[:digitos]
        return subcadena
    def nueva_subcadena_llave_dosificacion(self,llave_dofificacion,subcadena):
        number= len(llave_dofificacion)
        number_2= len(subcadena)
        digitos = number-number_2
        subcadena = llave_dofificacion[-digitos:]
        return subcadena
    def concatenar_datos_factura_cadena(self,digito,dato_factura,llave):

        subCadena= self.paso_dos_concatenar(llave,digito)
        dato_factura = str(dato_factura) + str(subCadena)
        self.Subcadena_llave = self.nueva_subcadena_llave_dosificacion(llave, subCadena)
        return dato_factura
    def aplicar_allegedRC4_sin_guion(self,message,key):
        resul = self.encryptMessageRC4(message, key);
        resul = resul.replace("-","");
        return resul;

    def encryptMessageRC4(self,message, key):
        state = []
        x = 0
        y = 0
        index1 = 0
        index2 = 0
        nmen = 0
        messageEncryption = ""
        for i in range(256):
            state.append(i)
        for i in range(256):
            index2 = int((ord(key[index1]) + int(state[i]) + index2) % 256)
            aux = state[i]
            state[i] = state[index2]
            state[index2] = aux
            index1 = int((index1 + 1) % len(key))
        for i in range(len(message)):
            x = (x + 1) % 256
            y = int((state[x] + y) % 256)
            aux = state[x]
            state[x] = state[y]
            state[y] = aux
            nmen = (ord(message[i])) ^ state[(state[x] + state[y]) % 256]
            nmenHex = hex(nmen).replace("0x","").upper()
            messageEncryption = messageEncryption + "-" + (("0" + nmenHex) if len(nmenHex) == 1 else nmenHex)
            rango = slice(1, len(messageEncryption))
        return messageEncryption[rango]

    def sumatoria_ASCII(self, cadena):
        st= 0
        stp1= 0
        position1=1
        stp2=0
        position2=2
        stp3=0
        position3=3
        stp4=0
        position4=4
        stp5=0
        position5=5
        contador =0
        for caracter in cadena:
            contador = contador + 1
            st = st + ord(caracter)
            if contador >= 1:
                if position1 == contador:
                    stp1 += ord(caracter)
                    position1 += 5
            if contador >= 2:
                if position2 == contador:
                    stp2 += ord(caracter)
                    position2 += 5
            if contador >= 3:
                if position3 == contador:
                    stp3 += ord(caracter)
                    position3 += 5
            if contador >= 4:
                if position4 == contador:
                    stp4 += ord(caracter)
                    position4 += 5
            if contador >= 5:
                if position5 == contador:
                    stp5 += ord(caracter)
                    position5 += 5

        return [st,stp1,stp2,stp3,stp4,stp5]
    def multilplicar_and_sumar_paso5(self,resultados_anteriores, digitos_verhoeff):
        sumatoria= 0
        i=0
        for no_hace_nada in digitos_verhoeff:
            sumatoria += int((float(resultados_anteriores[0]) * float(resultados_anteriores[1+i])) / (float(digitos_verhoeff[0+i])+1))
            i+=1
        return self.convertbase4(sumatoria)

    def convertbase4(self,value):
        diccionario_caracteres = [
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
            "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
            "U", "V", "W", "X", "Y", "Z", "a", "b", "c", "d",
            "e", "f", "g", "h", "i", "j", "k", "l", "m", "n",
            "o", "p", "q", "r", "s", "t", "u", "v", "w", "x",
            "y", "z", "+", "/"]

        cantidad = 1
        word = ""
        bandera = 0
        while cantidad > 0:
            cantidad = value / 64
            recordatorio = value % 64
            word = diccionario_caracteres[int(recordatorio)] + word
            value = cantidad
        bandera = False
        cadena = ''
        for caracter in word:
            if bandera:
                cadena += caracter
            elif caracter != '0':
                cadena += caracter
                bandera = True

        return cadena




