{
    'name': 'Enviar Correo Facturacion en Linea Bolivia',
    'version': '13.0.0.1.0',
    'category': 'Contabilidad',
    'description': '''
            Este Modulo cumple con el requisito de enviar la factura en linea  por Correo Bolivia
         ''',
    'summary': 'Con este Modulo se podra realizar el Envio de la facturacion en linea',
    'sequence': '10',
    'author': 'Sodigitalim',
    'maintainer': 'soluciones digitales para Impulsar su Negocio',
    'depends': ['account', 'base', 'sd_facturacion_en_linea_v13'],
    'data': [
        'security/grupo_reporte_facturacion.xml',
        'views/inherit_account_move.xml',
        'views/inherit_pos_config_view.xml',
        'reports/reports_facturacion_linea_siat.xml',
        'reports/report_factura_siat.xml',
        'reports/report_factura_siat_2.xml',
        'reports/report_factura_siat_rollo.xml',
        'reports/report_factura_siat_rollo_pos.xml',
        'data/data_ir_server_mail.xml',
        'data/data_paperformat.xml',
        'views/inherit_receipt_js.xml',
    ],
    'qweb': [
        'static/src/xml/inherit_pos_template.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
