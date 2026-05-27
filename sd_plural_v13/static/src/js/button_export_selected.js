odoo.define('sd_plural_v13.web_export_selected_button', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var core = require('web.core');
    var _t = core._t;

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var exportSelectedButton = $('<button>', {
                    class: 'btn btn-secondary o_list_button_export_selected',
                    text: _t('Export Selected'),
                });
                exportSelectedButton.appendTo(this.$buttons);
                exportSelectedButton.on('click', this._onExportSelected.bind(this));
            }
        },
        _onExportSelected: function () {
            var selectedRecordIDs = this.getSelectedIds();
            if (selectedRecordIDs.length === 0) {
                this.do_warn(_t("Warning"), _t("No records selected."));
                return;
            }

            var action = {
                type: 'ir.actions.act_url',
                url: '/web/export_selected?model=' + this.modelName + '&ids=' + selectedRecordIDs.join(','),
                target: 'self',
            };
            this.do_action(action);
        },
    });
});