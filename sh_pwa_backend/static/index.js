/*
 * PWA Backend - Odoo 13
 * ACTUALIZADO PARA NAVEGADORES ACTUALES
 *
 * CAMBIOS:
 * - Se elimina require('web.ajax') porque no se utilizaba.
 * - Se elimina el parámetro incorrecto "require" dentro de document.ready().
 * - Se registra explícitamente el scope "/".
 * - Se agrega manejo de errores.
 * - updateViaCache='none' ayuda a que Chrome consulte el SW actualizado.
 */

odoo.define('sh_pwa_backend.pwa', function (require) {
    'use strict';

    function registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('[PWA] Este navegador no soporta Service Worker.');
            return;
        }

        navigator.serviceWorker.register('/sw.js', {
            scope: '/',
            updateViaCache: 'none'
        }).then(function (registration) {
            console.log(
                '[PWA] Service Worker registrado correctamente. Scope:',
                registration.scope
            );

            // Solicita comprobar si existe una versión nueva.
            registration.update().catch(function (error) {
                console.warn(
                    '[PWA] No se pudo comprobar actualización del SW:',
                    error
                );
            });

        }).catch(function (error) {
            console.error(
                '[PWA] ERROR al registrar Service Worker:',
                error
            );
        });
    }

    // Registrar cuando la página terminó de cargar.
    if (document.readyState === 'complete') {
        registerServiceWorker();
    } else {
        window.addEventListener('load', registerServiceWorker);
    }
});