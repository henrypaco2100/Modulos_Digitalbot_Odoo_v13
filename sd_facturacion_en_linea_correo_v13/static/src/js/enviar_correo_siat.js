odoo.define('sd_facturacion_en_linea_correo_v13.custom_button_siat', function (require) {
"use strict";
    var screens = require('point_of_sale.screens');
    var ReceiptScreenWidget = screens.ReceiptScreenWidget;
    console.log('se llama al js')
    ReceiptScreenWidget.include({
        renderElement: function () {
            this._super.apply(this, arguments);
            self = this;
            console.log('this',this)
//            this.$('.button.correo').click(function(){
//                console.log('this',self)
//                self.click_handler();
//
//            });
            this.$('#enviar_correo_siat').click(_.bind(this.click_handler, this));
//            this.$('#enviar_correo_siat').on('click', function(){
//                alert("click")
//            })
        },

        click_handler: function () {
            // Llamar a la función de account.move
            console.log('llamo a la funcion',this)
            var self = this;
            var order = this.pos.get_order();
            console.log('order', order)
            if (order && order.move) {
                console.log('llamo a la funcion dentro if')
                var account_move_id = order.move.id;
                this._rpc({
                    model: 'account.move',
                    method: 'action_imprimir_factura_enviar_correo_siat_sudo',
                    args: [account_move_id],
                }).then(function (result) {
                    // Si deseas hacer algo con el resultado de la función, puedes hacerlo aquí
                }).catch(function (error) {
                    // Manejar el error si es necesario
                });
//                this._rpc({
//                    model: 'pos.config',
//                    method: 'actualizar_cantidad_productos',
//                    args: [self.pos.config_id, self.pos.config.default_location_src_id[0]],
//                }).then(function (result) {
//                    // Si deseas hacer algo con el resultado de la función, puedes hacerlo aquí
//                }).catch(function (error) {
//                    // Manejar el error si es necesario
//                });
            }
        },
    });

    return {
        ReceiptScreenWidget: ReceiptScreenWidget,
    };
});