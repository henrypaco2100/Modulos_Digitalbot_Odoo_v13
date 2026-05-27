odoo.define('sd_facturacion_en_linea_v13.inherit_models', function (require) {
    'use strict';

    var models = require('point_of_sale.models');
    var exports = {};

    models.load_fields("res.partner", ['st_nombre_compania_facturar','sd_codigo_tipo_documento', 'sd_extension', 'sd_nro_tarjeta']);
    models.load_fields("pos.payment.method", ['sd_es_tarjeta']);

    return models;
});