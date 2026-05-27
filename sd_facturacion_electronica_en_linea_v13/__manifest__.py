{
    'name': 'Facturacion Electronica en Linea Bolivia',
    'version': '1.0',
    'category': 'Contabilidad',
    'description': '''
            Este Modulo cumple con Todos los requisitos para realizar una "Factura Electronica en linea Bolivia "
         ''',
    'summary': 'Con este Modulo se podra realizar la "Factura Electronica en Linea Bolivia',
    'sequence': '10',
    'author': 'Sodigitalim',
    'maintainer': 'soluciones digitales para Impulsar su Negocio',
    'depends': ['account','sale','base'],
    'data': [
        'security/create_grupo_facturacion_electronica_linea.xml',
        'security/ir.model.access.csv',
        'view/heredar_diario_venta.xml',
        'view/heredar_a_contactos.xml',
        'view/electronic_billing.xml',
        'data/ir_sequence_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}