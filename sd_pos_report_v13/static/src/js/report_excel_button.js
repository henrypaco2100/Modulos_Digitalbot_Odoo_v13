odoo.define('sd_pos_report_v13.report_excel_button', function (require) {
    'use strict';

    var ReportAction = require('report.client_action');

    // ESI corrección: extender el visor HTML estándar de Odoo 13 sin reemplazarlo.
    // De esta forma se conserva el botón Imprimir nativo y añadimos Descargar Excel
    // únicamente cuando la vista previa fue abierta desde sd_pos_report_v13.
    ReportAction.include({
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var isSdPosPreview = Boolean(
                    self.data &&
                    self.data.sd_pos_report_excel &&
                    self.data.sd_pos_report_wizard_id
                );

                var $excelButton = self.$buttons.find('.o_sd_pos_report_excel');
                $excelButton.toggle(isSdPosPreview);

                if (isSdPosPreview) {
                    $excelButton.off('click.sd_pos_report_v13');
                    $excelButton.on('click.sd_pos_report_v13', function (ev) {
                        ev.preventDefault();
                        self._sd_download_excel_from_preview();
                    });
                }
            });
        },

        _sd_download_excel_from_preview: function () {
            var self = this;
            var wizardId = this.data && this.data.sd_pos_report_wizard_id;
            if (!wizardId) {
                return Promise.resolve();
            }

            // ESI corrección: reutilizar el mismo método XLSX del wizard. Así el Excel
            // usa los mismos POS, sesiones, fechas, pagos y totales que la vista HTML.
            return this._rpc({
                model: 'pos.details.wizard',
                method: 'action_export_xlsx',
                args: [[wizardId]],
            }).then(function (action) {
                if (action) {
                    return self.do_action(action);
                }
            });
        },
    });
});
