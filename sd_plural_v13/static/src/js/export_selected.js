odoo.define('sd_plural_v13.web_export_selected_button', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var core = require('web.core');
    var ajax = require('web.ajax');
    var _t = core._t;

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                var exportSelectedButton = $('<button>', {
                    class: 'btn btn-secondary o_list_button_export_selected',
                    text: _t('Exportar'),
                });
                exportSelectedButton.appendTo(this.$buttons);
                exportSelectedButton.on('click', function () {
                    var selectedRecordIDs = self.getSelectedIds();

                    if (selectedRecordIDs.length === 0) {
                        self.do_warn(_t("Warning"), _t("Seleccione al menos un registro."));
                        return;
                    }
                    let state = self.model.get(self.handle);
                    let defaultExportFields = self.renderer.columns.filter(field => field.tag === 'field' && state.fields[field.attrs.name].exportable !== false).map(field => field.attrs.name);
                    console.log('this', self)
                    ajax.jsonRpc('/web/export_selected', 'call', {
                        model: self.modelName,
                        ids: selectedRecordIDs,
                        field_names: defaultExportFields,
                    }).then(function (result) {
                        if (result.error) {
                            self.do_warn(_t("Error"), _t(result.error));
                        } else {
                            var blob = new Blob([result.content], { type: result.content_type });
                            var link = document.createElement('a');
                            link.href = URL.createObjectURL(blob);
                            link.download = result.filename;
                            link.click();
                        }
                    });
                });
            }
        },
    });
});
