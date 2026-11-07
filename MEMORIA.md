# Memoria de Proyecto - Don Juan Drive
- **Objetivo Principal:** Cliente nativo de Google Drive para Linux con interfaz Material 3 oficial (Bento Grid cards, floating popup y panel de Preferencias con soporte de Stream files y Mirror files sobre FUSE rclone).
- **Stack Técnico:** Python 3.14, PyQt6 (QtSvg, QtDBus), Material 3 QSS, rclone FUSE mount (--vfs-cache-mode full).

## Estado Actual (Última actualización: 2026-11-06)
- [x] Análisis REA del instalador oficial `GoogleDriveSetup.exe` (extracción de recursos vectoriales originales: mascota del perro `up_to_date.svg`, ilustraciones de atención y carpetas compartidas, iconos oficiales).
- [x] Implementación de `tray_popup.py` con interfaz Bento Cards idéntica al cliente oficial de Google Workspace / Google Drive Desktop.
- [x] Implementación de `preferences.py` con selector de sincronización ("Stream files" bajo demanda vs "Mirror files") y monitoreo de cuota de almacenamiento en tiempo real.
- [x] Compilación e instalación del binario standalone en `~/.local/bin/don-juan-drive`.

## Log de Cambios (Últimas 3 acciones)
1. Extracción e ingeniería inversa de assets SVG oficiales desde `.rsrc/RCDATA/101` del instalador Windows de Google Drive.
2. Creación de componentes `styles.py`, `tray_popup.py` (Bento Grid con 4 tarjetas cableadas) y `preferences.py` (Material 3).
3. Integración en `gui.py` (apertura al hacer clic en icono de bandeja) y compilación limpia con PyInstaller.

## Siguientes Pasos (To-Do)
- [ ] Validar interacción del usuario con la ventana flotante en la bandeja del sistema de KDE.
- [ ] Incorporar cambio dinámico de tema claro/oscuro según el esquema global de Plasma.

