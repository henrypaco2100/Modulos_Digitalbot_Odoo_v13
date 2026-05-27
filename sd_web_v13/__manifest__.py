{
    'name': 'Sd web v13',
    'category': 'Web',
    'summary': 'web modificaciones en la tienda, productos',
    'version': '13',
    'description': """Modificaciones y adicion de atributos en el template""",
    'depends': ['website','website_sale'],
    'author': 'SODIGITALIM',
    'data': [
        'static/src/xml/inherit_template_web_sale_product.xml',
        'static/src/xml/inherit_web_sale_item.xml',
        'views/inherit_product_template.xml',
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/website_sale_search.xml',
        'static/src/xml/website_sale_d.xml',
             ],
    'installable': True,
    'auto_install': False,
    'application': True,
}