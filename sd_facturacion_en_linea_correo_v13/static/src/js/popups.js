//odoo.define('sd_facturacion_en_linea_v13.popups', function (require) {
//    "use strict";
//
//    var PopupWidget = require('point_of_sale.popups');
//    var core = require('web.core');
//    var _t = core._t;
//
//    var gui = require("point_of_sale.gui");
//
////    var CardNumberPopupWidget = PopupWidget.extend({
//        template: 'CardNumberPopupWidget',
//        events: _.extend({}, PopupWidget.prototype.events, {
//            'click .button.confirm': 'click_confirm',
//            'click .button.cancel': 'click_cancel',
//        }),
//
//        show: function(options){
//            options = options || {};
//            this._super(options);
//            console.log('show de popup')
//            this.$('.card-number-input').focus();
//        },
//
//        click_confirm: function () {
//            var cardNumber = this.$('.card-number-input').val();
//            this.gui.close_popup();
//            if (this.options.confirm_callback) {
//                this.options.confirm_callback(cardNumber);
//            }
//        },
//
//        click_cancel: function () {
//            this.gui.close_popup();
//        },
//    });
//    gui.define_popup({
//        name: 'card_number_popup',
//        widget: CardNumberPopupWidget,
//    });
//    return {
//        CardNumberPopupWidget: CardNumberPopupWidget,
//    };
//
//});
