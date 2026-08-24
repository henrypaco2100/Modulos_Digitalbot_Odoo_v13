# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
#
# ACTUALIZADO PARA PWA / CHROME ACTUAL + ODOO 13
#
# CAMBIOS:
# - Standalone queda como opción por defecto.
# - Icono pequeño pasa de 32x32 a 192x192.
# - Icono grande continúa en 512x512.
# - PNG queda como mimetype por defecto.
# - Se agregan orientaciones modernas y la opción "any".
#
# IMPORTANTE:
# Cambiar el valor por defecto NO modifica automáticamente registros viejos.
# Después de actualizar el módulo, abra la configuración PWA y confirme:
#   Small Icon Size = 192x192
#   Big Icon Size   = 512x512
# y vuelva a guardar.

from odoo import fields, models


mime_selection = [
    ('image/png', 'image/png'),
    ('image/jpeg', 'image/jpeg'),
    ('image/webp', 'image/webp'),
    ('image/x-icon', 'image/x-icon'),
]

display_selection = [
    ('standalone', 'Standalone'),
    ('fullscreen', 'Fullscreen'),
    ('minimal-ui', 'Minimal UI'),
    ('browser', 'Browser'),
]

orientation_selection = [
    ('any', 'Any'),
    ('portrait', 'Portrait'),
    ('landscape', 'Landscape'),
    ('natural', 'Natural'),
]


class PWAConfig(models.Model):
    _name = 'sh.pwa.config'
    _description = 'PWA Configuration'

    name = fields.Char(
        required=True,
        default='Softhealer'
    )

    short_name = fields.Char(
        required=True,
        default='Softhealer'
    )

    theme_color = fields.Char(
        default='#DBDCDE'
    )

    background_color = fields.Char(
        default='#3367D6'
    )

    display = fields.Selection(
        selection=display_selection,
        default='standalone',
        required=True
    )

    orientation = fields.Selection(
        selection=orientation_selection,
        default='any'
    )

    # Chromium actual espera un icono de 192x192.
    icon_small = fields.Binary(
        string='Icon 192x192',
        help='PNG recomendado. Debe ser realmente de 192x192 píxeles.'
    )

    icon_small_mimetype = fields.Selection(
        selection=mime_selection,
        default='image/png',
        help='Para PWA se recomienda image/png.'
    )

    icon_small_size = fields.Char(
        string='Small Icon Size',
        default='192x192',
        help='Debe coincidir con el tamaño real de la imagen.'
    )

    # Chromium actual espera además un icono de 512x512.
    icon = fields.Binary(
        string='Icon 512x512',
        help='PNG recomendado. Debe ser realmente de 512x512 píxeles.'
    )

    icon_mimetype = fields.Selection(
        selection=mime_selection,
        default='image/png',
        help='Para PWA se recomienda image/png.'
    )

    icon_size = fields.Char(
        string='Big Icon Size',
        default='512x512',
        help='Debe coincidir con el tamaño real de la imagen.'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id.id
    )

    icon_iphone = fields.Binary(
        help='Icon for iPhone / Apple Touch Icon.',
        string='Icon for iPhone'
    )