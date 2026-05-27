odoo.define('sd_libro_compra_venta.custom_form', function (require) {
    "use strict";

    var FormController = require('web.FormController');

    FormController.include({
        _updateButtons: function () {
            this._super.apply(this, arguments);
            var self = this;

            var $pageToToggle = this.renderer.arch.attrs.options.page_to_toggle;
            if ($pageToToggle) {
                var fieldName = $pageToToggle.field;
                var targetPage = $pageToToggle.page;

                this.renderer.on('change', this, function (event) {
                    if (event.data.changes[fieldName]) {
                        self.renderer.$('.page').hide();
                        self.renderer.$('.o_form_page[name="' + targetPage + '"]').show();
                    }
                });
            }
        },
    });
});