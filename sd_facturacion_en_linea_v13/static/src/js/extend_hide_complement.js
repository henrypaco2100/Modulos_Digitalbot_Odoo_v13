odoo.define('sd_facturacion_en_linea_v13.BaseWidget', function (require) {
    "use strict";

    var core = require('web.core');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    console.log("base widget");
    var _t = core._t;

    var CustomPosWidget = PosBaseWidget.extend({
        template: 'sd_pos_client_details_edit',

         init: function (parent, options) {
            this._super(parent, options);
            this.is_sd_extension_hidden = false;  // Campo oculto inicialmente
            this.sdTipoDocumento = '1';
        },

        renderElement: function () {
            console.log('render')
            this._super();
            this.$('select[name="tipo_identificacion"]').on('change', this.handleSelectChange.bind(this));
        },

        handleSelectChange: function (event) {
            console.log('handle')
            var selectedOption = $(event.currentTarget).val();
            this.is_sd_extension_hidden = selectedOption !== '1';  // Ocultar campo si no es Carnet identidad
            this.renderElement();
        },

    });

    return CustomPosWidget;
});

