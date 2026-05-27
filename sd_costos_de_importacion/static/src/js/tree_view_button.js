//odoo.define('st_kardex.tree_view_button', function (require){
//    "use strict";
//
//    var ajax = require('web.ajax');
//    var ListController = require('web.ListController');
//
//    var rpc = require('web.rpc')
//
//    ListController.include({
//        renderButtons: function($node) {
//            this._super.apply(this, arguments);
//            var self = this;
//            if (this.$buttons) {
//                this.$buttons.find('.oe_new_custom_button').click(this.proxy('action_def')
//
//                });
//
//            }
//            action_def: function () {
//                var self =this
//                rpc.query({
//                    model: 'stock.move.line',
//                    method: 'action_actualizar_valoracion',
//                    args: [false,]
//                    });
//                },
//        },
//    });
//});
//
odoo.define('st_kardex.tree_view_button', function (require) {
"use strict";

var core = require('web.core');
var ListController = require('web.ListController');

var _t = core._t;
var qweb = core.qweb;

//var ValuationValidationController = ListController.extend({
//    events: _.extend({
//        'click .oe_new_custom_button': '_onValidateValuation'
//    }, ListController.prototype.events),

    ListController.include({
        renderButtons: function($node) {
            this._super.apply(this, arguments);
            var self = this;
            if (this.$buttons) {
                this.$buttons.find('.oe_new_custom_button').click(this.proxy('_onValidateValuation'))
            },
            },


    _onValidateValuation: function () {
        var self = this;
        var prom = Promise.resolve();

        prom.then(function () {
            self._rpc({
                model: 'stock.move.line',
                method: 'action_actualizar_valoracion',
//                args: [self.move_id]
            })
        });
    },
});


});
