# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "PWA (Progressive Web Application) Backend",
    
    "author": "Softhealer Technologies",
    
    "website": "https://www.softhealer.com",    
    
    "support": "support@softhealer.com",   

    "version": "13.0.3",
    
    "category": "Extra Tools",
    
    "summary": "Get Backend PWA App, Build PWA Backend App From Website, Progressive Web Apps Backend Module, Make Backend PWA From Odoo, Create PWA Backend Application Odoo",
        
    "description": """The PWA (progressive web application) backend works like a normal application on the mobile. It allows you to adjust the custom style as your requirement. We provide icon size, name, display orientation, colors, etc options to make quickly app format. You get a combination of a native app with the website. PWA Backend Odoo, Get Backend PWA App, Build PWA Backend App From Website, Progressive Web Apps Backend Module, Make Backend PWA From Odoo, Create PWA Backend Application Odoo, Get Backend PWA App, Build PWA Backend App From Website, Progressive Web Apps Backend Module, Make Backend PWA From Odoo, Create PWA Backend Application Odoo""",
     
    "depends": ['base','web'],
        
    "data": [
        "data/pwa_configuraion_data.xml",
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/pwa_configuration_view.xml",
    ],
    "images": ["static/description/background.png",], 
    "live_test_url": "https://youtu.be/7fCQN-N5k9w",
    "installable": True,    
    "auto_install": False,    
    "application": True,  
    "price": "50",
    "currency": "EUR"       
}
