# Memoria de Proyecto - Don Juan Drive
- **Objetivo Principal:** Cliente nativo de Google Drive para Linux con interfaz Material 3 oficial (Bento Grid cards, floating popup y panel de Preferencias con soporte de Stream files y Mirror files sobre FUSE rclone).
- **Stack Técnico:** Python 3.14, PyQt6 (QtSvg, QtDBus), Material 3 QSS, rclone FUSE mount (--vfs-cache-mode full).

## Estado Actual (Última actualización: 2026-11-06)
- [x] Análisis REA del instalador oficial `GoogleDriveSetup.exe` (extracción de recursos vectoriales originales: mascota del perro `up_to_date.svg`, ilustraciones de atención y carpetas compartidas, iconos oficiales).
- [x] Implementación de `tray_popup.py` con interfaz Bento Cards idéntica al cliente oficial de Google Workspace / Google Drive Desktop.
- [x] Implementación de `preferences.py` con selector de sincronización ("Stream files" vs "Mirror files") y monitoreo de cuota de almacenamiento.
- [x] Corrección integral del visor de cuenta de Google (`account_dialog.py`), eliminando cierres inesperados y mostrando almacenamiento y usuario en tiempo real.
- [x] Integración en el explorador Dolphin (Lugares de KDE e icono SVG oficial de Google Drive vinculado a `~/Google Drive`).
- [x] Compilación e instalación del binario standalone en `~/.local/bin/don-juan-drive` (PID activo).
- [x] Publicación y sincronización completa del repositorio en GitHub (`https://github.com/jcrbaustin/Don-Juan-Drive`).

## Log de Cambios (Últimas 3 acciones)
1. Corrección del visor de cuenta: creación de `GoogleAccountDialog` en `account_dialog.py`, soporte de cuota `rclone about` y vinculación segura al botón de avatar en `tray_popup.py` y `gui.py`.
2. Integración nativa con Dolphin y gestores de archivos: registro en `user-places.xbel` y bookmarks GTK con icono vectorizado oficial `google-drive.svg`.
3. Compilación limpia a binario `~/.local/bin/don-juan-drive`, ejecución en segundo plano y push del código a GitHub (`jcrbaustin/Don-Juan-Drive`).

## Siguientes Pasos (To-Do)
- [ ] Validar interacción del usuario con el modal de cuenta y pop-up flotante en KDE Plasma.
- [ ] Incorporar cambio dinámico de tema claro/oscuro según el esquema global de Plasma.

