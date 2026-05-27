odoo.define('sd_facturacion_en_linea_correo_v13.inherit_pos_order', function (require) {
    'use strict';
    // para la venta emergente
    var gui = require('point_of_sale.gui');
    var PopupWidget = require('point_of_sale.popups');
    var PaymentScreenWidget = require('point_of_sale.screens').PaymentScreenWidget;

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var exports = models.exports;
//    var receipt = {}
    var PosModel = models.PosModel.prototype;
    var Order = models.Order.prototype;
    var Orderline = models.Orderline.prototype;
    var rpc = require('web.rpc');
//    var OrderScreen = screens;

    var field_utils = require('web.field_utils');
    var utils = require('web.utils');
//    var QRCode = require('qrcode');
    var round_di = utils.round_decimals;
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

//    //enviar correo
//    var CustomButton = PosComponent.extend({
//        renderElement: function () {
//            this.$('#enviar_correo_siat').click(_.bind(this.click_handler, this));
//        },
//
//        click_handler: function () {
//            // Llamar a la función del modelo Python
//            var self = this;
//            var order = this.env.pos.get_order();
//            console.log('orden desde boton', order)
//            var partner = order.get_client();
//            if (partner) {
////                rpc.query({
////                    model: 'res.partner',
////                    method: 'custom_function',
////                    args: [partner.id],
////                }).then(function (result) {
////                    // Si deseas hacer algo con el resultado de la función, puedes hacerlo aquí
////                }).catch(function (error) {
////                    // Manejar el error si es necesario
////                });
//            }
//        },
//    });

    // guarda la tarjeta con formato
    screens.ClientListScreenWidget.include({
        save_client_details: function(partner) {
            var self = this;
            this._super(partner);
            if (partner) {
                if (partner.sd_nro_tarjeta) {
                    var nro_formato = self.pos.format_sd_nro_tarjeta(partner.sd_nro_tarjeta);
    //                var nro_formato = partner.sd_nro_tarjeta;
                    console.log('con formato', nro_formato);
                    console.log('self', self)
                    partner.sd_nro_tarjeta = nro_formato;
                    this.gui.show_popup('confirm', {
                        title: _t('Save Changes'),
                        body: _t('¿Estás seguro/a de que quieres guardar los cambios en el cliente?'),
                        confirm: function () {
                            self.pos.patchPartner(partner.id, nro_formato).then(function () {
                                console.log('Changes saved successfully!');
                            }).catch(function (error) {
                                console.error('Error while saving changes:', error);
                            });
                        },
                        cancel: function () {
                            // Restore the original value or take any other action if needed
                            console.log('Changes not saved.');
                        },
                    });
                }
            }
        },
    });
//    console.log('hello init',screens);
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            PosModel.initialize.call(this, session, attributes);
            // Agrega la variable this.move
            this.move = null;

            var self = this;

            this.format_sd_nro_tarjeta = function (value) {
                if (value) {
                    console.log('entro al if de format')
                    return value.slice(0, 4) + '00000000' + value.slice(-4);
                }
                return value;
            };

            // Llamada inicial para formatear el campo cuando el cliente ya está seleccionado al cargar el POS
//            if (this.get('selectedClient')){
//                var partner = this.get('selectedClient').get();
//            }
//            if (partner) {
//                var nro_formato = this.format_sd_nro_tarjeta(partner.sd_nro_tarjeta);
//                this.get('selectedOrder').set_client(partner);
//                this.get('selectedOrder').set_invoice_number(nro_formato);
//            }
        },
        patchPartner: function (partner_id, sd_nro_tarjeta) {
            return rpc.query({
                model: 'res.partner',
                method: 'write',
                args: [partner_id, { 'sd_nro_tarjeta': sd_nro_tarjeta }],
            });
        },
    });

    function obtener_tipo_factura(tipo_factura) {
        var res = "FACTURA CON DERECHO A CREDITO FISCAL";
        if (tipo_factura != '1') {
            res = "FACTURA SIN DERECHO A CREDITO FISCAL";
        }
        return res;
    }
    function esperar(segundos) {
        return new Promise(resolve => {
//            console.log('espera 2seg')
            setTimeout(resolve, segundos * 1000);
        });
    }
    function obtener_nro_documento(nro_documento, sd_extension) {
        var res = nro_documento;
        if (sd_extension){
            res = nro_documento + " - " +sd_extension;
        }
        return res;
    }
    function obtener_tipo_emision(tipo_emision) {
        var res_emision;
        if (tipo_emision == 1){
            res_emision = 'Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea';
        }else{
            res_emision = 'Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido fuera de linea, verifique su envio con su proveedor o en la página web www.impuestos.gob.bo';
        }
        return res_emision;
    }
    function ajustar_fecha_emision(fecha_emision){
        // Crear objeto Date con la fecha en cadena
        var fecha = new Date(fecha_emision);

        // Obtener la diferencia en minutos entre la hora local y la hora UTC del cliente
        var ajusteZonaHoraria = fecha.getTimezoneOffset();

        // Convertir la diferencia a milisegundos (multiplicar por -60000)
        ajusteZonaHoraria = ajusteZonaHoraria * -60000;

        // Obtener la hora actual en milisegundos
        var horaActual = fecha.getTime();

        // Sumar el ajuste de zona horaria a la hora actual
        var horaAjustada = horaActual + ajusteZonaHoraria;

        // Crear un nuevo objeto Date con la hora ajustada
        var fechaAjustada = new Date(horaAjustada);

        // Obtener los componentes de fecha y hora ajustados
        var año = fechaAjustada.getFullYear();
        var mes = (fechaAjustada.getMonth() + 1).toString().padStart(2, '0'); // Añadir padding al mes
        var día = fechaAjustada.getDate().toString().padStart(2, '0'); // Añadir padding al día
        var hora = fechaAjustada.getHours();
        var minuto = fechaAjustada.getMinutes().toString().padStart(2, '0'); // Añadir padding a los minutos
        var segundo = fechaAjustada.getSeconds().toString().padStart(2, '0'); // Añadir padding a los segundos

        // Calcular el meridiano (AM o PM)
        var meridiano = hora < 12 ? "AM" : "PM";

        // Formatear la hora ajustada como cadena (formato de 12 horas)
        hora = hora % 12; // Convertir la hora al formato de 12 horas
        hora = hora || 12; // Si la hora es 0, asignar 12
        hora = hora.toString().padStart(2, '0');
        // Formatear la fecha y hora ajustadas como cadena
        var fechaAjustadaCadena = `${año}-${mes}-${día} ${hora}:${minuto}:${segundo} ${meridiano}`;

//        console.log(fechaAjustadaCadena);
        return fechaAjustadaCadena;
    }
//    function generateFacturaQRCode(url) {
//      var qr = new QRCode(document.getElementById("qr-container"), {
//        width: 150,
//        height: 150,
//      });
//
//      qr.makeCode(url).then(function(qr){
//        console.log('se resolvio', qr);
//      }).catch(function(error){
//        console.error(error);
//      }); // Reemplaza la URL con tu contenido
//    }


    models.Order = models.Order.extend({
        initialize: function (attributes,options) {
            Order.initialize.call(this, attributes,options);
            // Agrega la variable this.move
            this.move = null;
            this.order_id = null;
            this.nro_tarjeta = null;
            console.log('order inicial',this);
            if (this.pos.config.sd_fcb_es_electronico){
                this.to_invoice = true;
            }
        },
        es_tarjeta: function(){
            var es_tarjeta = false;
            for (var paymentmodel of this.paymentlines.models) {
                if (paymentmodel.payment_method.sd_es_tarjeta) {
                    es_tarjeta = true;
                }
            }
            return es_tarjeta;
        },
        obtenerOrder: async function (name) {
            var order = null;
            order = await rpc.query({
                model: 'pos.order',
                method: 'search_read',
                args: [[['pos_reference', '=', name]]],
                kwargs: {}
            });
            return order;
        },
        obtenerAccountMove: async function (move_id) {
            var move = null;
            move = await rpc.query({
                model: 'account.move',
                method: 'search_read',
                args: [[['id', '=', move_id]]],
                kwargs: {}
            });
            return move;
        },
        decimal_format_siat: function(amount){
            if (typeof amount === 'number') {
                amount = round_di(amount,2).toFixed(2);
                amount = field_utils.format.float(round_di(amount, 2), {digits: [69, 2]});
            }
            return amount;
        },
        convertirNumeroALetras: function(numero) {
          // Arrays para la representación de las unidades, decenas y otros valores especiales
          var unidades = ['', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve'];
          var especiales = ['', 'once', 'doce', 'trece', 'catorce', 'quince', 'dieciséis', 'diecisiete', 'dieciocho', 'diecinueve'];
          var decenas = ['', 'diez', 'veinte', 'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa'];
          var centenas = ['', 'ciento', 'doscientos', 'trescientos', 'cuatrocientos', 'quinientos', 'seiscientos', 'setecientos', 'ochocientos', 'novecientos'];
          var entero = Math.floor(numero);
          var decimal = Math.round((numero - entero) * 100);
          var parte_decimal = null;
          numero = entero;
          //funcion auxiliar para manejar la parte decimal
          function obtenerFraccionEnLetras(decimal) {
              var fraccionEnLetras = "";
              if (decimal >= 0 && decimal < 100) {
                fraccionEnLetras = " " + decimal.toString().padStart(2, "0") + "/100";
              }
              return fraccionEnLetras;
            }
          parte_decimal = obtenerFraccionEnLetras(decimal);
          // Función auxiliar para convertir un número menor a 1000 en letras
          function convertirMenorATresCifras(numero) {
            var letras = '';

            if (numero >= 100) {
              var centena = Math.floor(numero / 100);
              letras += centenas[centena] + ' ';
              numero %= 100;
            }

            if (numero >= 20) {
              var decena = Math.floor(numero / 10);
              letras += decenas[decena] + ' ';
              numero %= 10;
            }

            if (numero > 0 && numero < 10) {
              letras += unidades[numero] + ' ';
            } else if (numero >= 10 && numero < 20) {
              letras += especiales[numero - 10] + ' ';
            }

            return letras.trim();
          }

          // Función principal para convertir el número en letras
          var letras = '';

          if (numero === 0) {
            letras = 'Cero';
          } else if (numero < 0) {
            letras = 'menos ' + convertirNumeroALetras(Math.abs(numero));
          } else {
            if (numero >= 1000000) {
              var millones = Math.floor(numero / 1000000);
              letras += convertirMenorATresCifras(millones) + ' Millón ';
              numero %= 1000000;
            }

            if (numero >= 1000) {
              var miles = Math.floor(numero / 1000);
              letras += convertirMenorATresCifras(miles) + ' Mil ';
              numero %= 1000;
            }

            letras += convertirMenorATresCifras(numero);
          }

          return letras.trim()+' '+parte_decimal;
        },
        generateFacturaQRCode: async function (url) {
        async function checkQRContainer() {

            var div = document.getElementById("qr-container-test-3");
            if (div) {

                if (url){
                      // Crear un nuevo elemento para el código QR
                      // Eliminar los elementos existentes
                      var qrcode = document.getElementById("qrcode");
                      if (qrcode) {
                        qrcode.parentNode.removeChild(qrcode);

                      }
                      // Crear los nuevos elementos
                      var qrCodeElement = document.createElement("div");
                      qrCodeElement.id = "qrcode";
                      div.appendChild(qrCodeElement);

                      // Generar el código QR
                      var qrcodegen = new QRCode(qrCodeElement, {
                        text: url,
                        width: 128,
                        height: 128,
                      });
//                      console.log('mostrar div',div);
                }
            } else {
                // El elemento aún no está disponible, volver a verificar después de un intervalo de tiempo
//                console.log('else- qr container');
                setTimeout(await checkQRContainer, 100); // Esperar 100ms antes de volver a verificar
            }
        }

        setTimeout( await checkQRContainer, 200);

        },
        export_for_printing: function() {
            var receipt = Order.export_for_printing.call(this);
            var pos_config_dict = { en_linea:this.pos.config.sd_fcb_es_electronico, to_invoice: this.to_invoice };
            receipt.config = pos_config_dict;
            if (this.to_invoice) {
                var self = this;
//                var pos_config_dict = { en_linea: self.pos.config.sd_fcb_es_electronico, to_invoice: self.to_invoice };
//                receipt.config = pos_config_dict;
                async function obtener_receipt_test(receipt) {
                    self.order_id = await self.obtenerOrder(self.name);
//                    console.log('order-id-test-2222', self.order_id);
                    var move = await self.obtenerAccountMove(self.order_id[0].account_move[0]);
                    self.move = move[0];
//                    console.log('account_mov', self.move);
//                    await generateFacturaQRCode(self.move.sd_url_factura);
                    var move_dict = {
                        tipo_factura: obtener_tipo_factura(self.move.sd_tipo_factura),
                        nombre_company: self.move.sd_nombre_company,
                        sucursal: self.move.sd_sucursal_str,
                        punto_venta: self.move.sd_nro_pv,
                        direccion: self.move.sd_direccion,
                        celular_company: self.move.sd_nro_company,
                        municipio: self.move.sd_municipio,
                        nit_emisor: self.move.sd_nit_emisor,
                        nro_factura: self.move.sd_nro_factura_siat,
                        cuf: self.move.sd_cuf,
                        nombre_facturado: self.move.sd_nombre_facturado,
                        nro_documento: obtener_nro_documento(self.move.sd_nro_documento_facturado, self.move.sd_extension),
                        codigo_cliente: self.move.partner_id[0],
                        fecha_emision: ajustar_fecha_emision(self.move.sd_fecha_emision),
                        leyenda_emision: obtener_tipo_emision(self.move.sd_tipo_emision),
                        leyenda_factura: self.move.sd_leyenda_id[1],
                        url_factura: self.move.sd_url_factura,
                    };
//                    generateFacturaQRCode(self.move.sd_url_factura);
                    receipt.move = move_dict;

//                    console.log('receipt desde funcion', receipt)
                    await self.generateFacturaQRCode(move_dict['url_factura']);
                    return receipt;
                }

                return obtener_receipt_test(receipt);
            } else {
                return receipt;
            }
        },
    });
    models.Orderline = models.Orderline.extend({
        export_for_printing: function() {
            var order_line = Orderline.export_for_printing.call(this);
            order_line.unit_name_siat = this.get_unit().sd_unidad_medida_id[1];
            order_line.code_product = this.get_product().default_code;
            return order_line;
        }

    })

    var ReceiptScreenWidget = screens.ReceiptScreenWidget;
    var MyReceiptScreenWidget = ReceiptScreenWidget.include({
//        console.log('parte del codigo');
         get_receipt_render_env: async function() {
            var order = this.pos.get_order();
            var receipt = await order.export_for_printing();
//            console.log('nueva funcion asincrona', receipt);
            var renderEnv = {
                widget: this,
                pos: this.pos,
                order: order,
                receipt: receipt,
                orderlines: order.get_orderlines(),
                paymentlines: order.get_paymentlines(),
            };

            return renderEnv;
        },
        print_html: async function () {
//            console.log('print html funcion')
            var receipt = QWeb.render('OrderReceipt', await this.get_receipt_render_env());

            this.pos.proxy.printer.print_receipt(receipt);
            this.pos.get_order()._printed = true;
        },
        render_receipt: async function() {
//            console.log('renderizado de recibo');
            this.$('.pos-receipt-container').html(QWeb.render('OrderReceipt', await this.get_receipt_render_env()));
        }
    });
//    console.log('modulo',MyReceiptScreenWidget );
    screens.ReceiptScreenWidget = MyReceiptScreenWidget;

// para la ventana emergente

//    gui.define_popup({ name: 'card_number_popup', widget: CardNumberPopupWidget });
//
//    posModel.load_fields('sale.order', ['card_number_field']);

    return models;
//    return {
//        models: models,
//        ReceiptScreenWidget: MyReceiptScreenWidget
//    };
});