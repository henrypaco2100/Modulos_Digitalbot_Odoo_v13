# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
#
# ACTUALIZADO PARA PWA / CHROME ACTUAL + ODOO 13
#
# CAMBIOS PRINCIPALES:
# 1) Manifest con Content-Type correcto: application/manifest+json.
# 2) Se agrega "id" y "prefer_related_applications".
# 3) Se mantienen los iconos configurables 192x192 y 512x512.
# 4) Si el mimetype no está guardado, se asume image/png.
# 5) Service Worker simplificado para NO cachear páginas dinámicas de Odoo.
#    El SW antiguo usaba cache-first y podía dejar JS viejo almacenado.
# 6) Se corrigen nombres de métodos de rutas de iconos.
# 7) Se usan respuestas con no-cache para manifest y service worker,
#    para facilitar actualizaciones del módulo.
#
# IMPORTANTE:
# Para que Chrome considere la web instalable como PWA, configura:
# - icon_small: PNG real de 192x192
# - icon: PNG real de 512x512
# No declares un tamaño distinto al tamaño real del archivo.

import json
import base64
from io import BytesIO

from odoo import http


class Main(http.Controller):

    def _get_manifest_json(self, company):
        """Construye el Web App Manifest para la compañía."""
        if not company:
            company = 1

        try:
            company_id = int(str(company).split(',')[0])
        except (TypeError, ValueError):
            company_id = 1

        pwa_config = http.request.env['sh.pwa.config'].sudo().search(
            [('company_id', '=', company_id)],
            limit=1
        )

        # Valores mínimos seguros.
        vals = {
            "id": "/web",
            "name": "Softhealer-APP",
            "short_name": "SH-APP",
            "scope": "/",
            "start_url": "/web",
            "background_color": "#FFFFFF",
            "theme_color": "#875A7B",
            "display": "standalone",
            "prefer_related_applications": False,
            "icons": [],
        }

        if pwa_config:
            if pwa_config.name:
                vals["name"] = pwa_config.name

            if pwa_config.short_name:
                vals["short_name"] = pwa_config.short_name

            if pwa_config.theme_color:
                vals["theme_color"] = pwa_config.theme_color

            if pwa_config.background_color:
                vals["background_color"] = pwa_config.background_color

            if pwa_config.display:
                vals["display"] = pwa_config.display

            if pwa_config.orientation:
                vals["orientation"] = pwa_config.orientation

            icon_list = []

            # ICONO PEQUEÑO: debe ser realmente 192x192.
            if pwa_config.icon_small:
                icon_list.append({
                    "src": "/sh_pwa_backend/pwa_icon_small/%s" % company_id,
                    "type": pwa_config.icon_small_mimetype or "image/png",
                    "sizes": pwa_config.icon_small_size or "192x192",
                    "purpose": "any"
                })

            # ICONO GRANDE: debe ser realmente 512x512.
            if pwa_config.icon:
                icon_list.append({
                    "src": "/sh_pwa_backend/pwa_icon/%s" % company_id,
                    "type": pwa_config.icon_mimetype or "image/png",
                    "sizes": pwa_config.icon_size or "512x512",
                    "purpose": "any"
                })

            vals["icons"] = icon_list

        # Fallback antiguo del módulo.
        # NOTA: este icono solo cubre 192x192. Para instalación PWA completa
        # en Chromium actual, se recomienda cargar además el icono 512x512
        # desde la configuración del módulo.
        if not vals["icons"]:
            vals["icons"] = [{
                "src": "/sh_pwa_backend/static/icon/sh.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any"
            }]

        return vals

    @http.route(
        '/manifest.json/<string:cid>',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    def manifest_http(self, cid=None, **post):
        """Entrega el manifest con MIME correcto."""
        manifest = json.dumps(
            self._get_manifest_json(cid),
            ensure_ascii=False
        )

        return http.request.make_response(
            manifest,
            headers=[
                ('Content-Type', 'application/manifest+json; charset=utf-8'),
                ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                ('Pragma', 'no-cache'),
                ('Expires', '0'),
            ]
        )

    @http.route(
        '/sw.js',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    def sw_http(self):
        """
        Service Worker.

        Se elimina el cache-first del módulo original porque Odoo es una
        aplicación dinámica y ese cache podía conservar index.js antiguo.

        Para el objetivo de instalar/abrir Odoo como aplicación, basta con
        registrar correctamente el SW y permitir que tome control.
        """
        js = r"""
self.addEventListener('install', function (event) {
    self.skipWaiting();
});

self.addEventListener('activate', function (event) {
    event.waitUntil(self.clients.claim());
});

/*
 * No interceptamos las peticiones de Odoo con cache-first.
 * Así evitamos sesiones, assets o vistas antiguas guardadas por el SW.
 */
"""

        return http.request.make_response(
            js,
            headers=[
                ('Content-Type', 'application/javascript; charset=utf-8'),
                ('Service-Worker-Allowed', '/'),
                ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                ('Pragma', 'no-cache'),
                ('Expires', '0'),
            ]
        )

    def get_icon(self, field_icon, company):
        """Devuelve un icono almacenado en sh.pwa.config."""
        try:
            company_id = int(str(company).split(',')[0])
        except (TypeError, ValueError):
            company_id = 1

        pwa_config = http.request.env['sh.pwa.config'].sudo().search(
            [('company_id', '=', company_id)],
            limit=1
        )

        if not pwa_config:
            return http.request.not_found()

        if field_icon == 'icon_small':
            icon = pwa_config.icon_small
            icon_mimetype = pwa_config.icon_small_mimetype or 'image/png'
        else:
            icon = pwa_config.icon
            icon_mimetype = pwa_config.icon_mimetype or 'image/png'

        if not icon:
            return http.request.not_found()

        try:
            icon_bytes = BytesIO(base64.b64decode(icon)).read()
        except Exception:
            return http.request.not_found()

        return http.request.make_response(
            icon_bytes,
            headers=[
                ('Content-Type', icon_mimetype),
                ('Cache-Control', 'public, max-age=86400'),
            ]
        )

    @http.route(
        '/sh_pwa_backend/pwa_icon/<string:cid>',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    def icon(self, cid=None, **post):
        """Icono grande, normalmente 512x512."""
        return self.get_icon('icon', cid)

    @http.route(
        '/sh_pwa_backend/pwa_icon_small/<string:cid>',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    def icon_small(self, cid=None, **post):
        """Icono pequeño, normalmente 192x192."""
        return self.get_icon('icon_small', cid)

    @http.route(
        '/iphone.json/<string:cid>',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    def iphone_http(self, cid=None, **post):
        """Devuelve el apple-touch-icon configurado."""
        try:
            company_id = int(str(cid).split(',')[0])
        except (TypeError, ValueError):
            company_id = 1

        pwa_config = http.request.env['sh.pwa.config'].sudo().search(
            [('company_id', '=', company_id)],
            limit=1
        )

        if not pwa_config or not pwa_config.icon_iphone:
            return http.request.not_found()

        icon_mimetype = pwa_config.icon_mimetype or 'image/png'

        try:
            icon_bytes = BytesIO(
                base64.b64decode(pwa_config.icon_iphone)
            ).read()
        except Exception:
            return http.request.not_found()

        return http.request.make_response(
            icon_bytes,
            headers=[
                ('Content-Type', icon_mimetype),
                ('Cache-Control', 'public, max-age=86400'),
            ]
        )