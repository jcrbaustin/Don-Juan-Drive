import os
import subprocess
from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QDialog, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QHBoxLayout, 
                             QFileDialog, QTextEdit, QMainWindow, QWidget, QGroupBox, QCheckBox)
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtCore import QObject

from backend import DriveBackend

import os
import sys
import socket
import time
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class MonitorRed(QThread):
    conexion_cambiada = pyqtSignal(bool)
    
    def run(self):
        estado_anterior = None
        while True:
            try:
                try:
                    # Intenta abrir un socket rápido para comprobar internet
                    socket.create_connection(("8.8.8.8", 53), timeout=2)
                    estado_actual = True
                except OSError:
                    estado_actual = False
                    
                if estado_actual != estado_anterior:
                    self.conexion_cambiada.emit(estado_actual)
                    estado_anterior = estado_actual
                    
                time.sleep(10)
            except Exception as e:
                print(f"Excepción en el hilo de red: {e}")
                time.sleep(10)

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso (ej. imágenes), funciona para entorno dev y PyInstaller."""
    try:
        # PyInstaller almacena los recursos en una carpeta temporal _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class LogWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registros de Rclone - Don Juan Drive")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        # Usar fuente monoespaciada para facilitar la lectura de los logs
        font = QFont("Monospace")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.text_edit.setFont(font)
        
        layout.addWidget(self.text_edit)
        
        btn_clear = QPushButton("Limpiar Registros")
        btn_clear.clicked.connect(self.text_edit.clear)
        layout.addWidget(btn_clear)

    def append_log(self, text):
        self.text_edit.append(text)

class ConfigWindow(QMainWindow):
    def __init__(self, backend, tray_app=None):
        super().__init__()
        self.backend = backend
        self.tray_app = tray_app
        self.setWindowTitle("Configuración - Don Juan Drive")
        self.setMinimumSize(450, 450)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Nombre del remoto
        remote_layout = QHBoxLayout()
        remote_layout.addWidget(QLabel("Nombre Remoto (rclone):"))
        self.remote_input = QLineEdit(self.backend.remote_name)
        remote_layout.addWidget(self.remote_input)
        layout.addLayout(remote_layout)
        
        # Ruta de Montaje
        mount_layout = QHBoxLayout()
        mount_layout.addWidget(QLabel("Ruta de Montaje:"))
        self.mount_input = QLineEdit(self.backend.mount_path)
        btn_browse = QPushButton("Explorar")
        btn_browse.clicked.connect(self.browse_path)
        mount_layout.addWidget(self.mount_input)
        mount_layout.addWidget(btn_browse)
        layout.addLayout(mount_layout)
        
        # Tamaño de Caché
        cache_layout = QHBoxLayout()
        cache_layout.addWidget(QLabel("Tamaño Máximo de Caché:"))
        self.cache_input = QLineEdit(self.backend.cache_size)
        cache_layout.addWidget(self.cache_input)
        layout.addLayout(cache_layout)
        
        # Botones de Acción
        action_layout = QHBoxLayout()
        self.btn_rclone_cfg = QPushButton("Iniciar Sesión con Google")
        self.btn_rclone_cfg.clicked.connect(self.run_config)
        action_layout.addWidget(self.btn_rclone_cfg)
        
        btn_verify = QPushButton("Verificar Conexión")
        btn_verify.clicked.connect(self.verificar_nueva_cuenta)
        action_layout.addWidget(btn_verify)
        
        self.label_estado = QLabel("Estado: Sin verificar")
        self.label_estado.setStyleSheet("color: gray; font-weight: bold;")
        action_layout.addWidget(self.label_estado)
        
        layout.addLayout(action_layout)
        
        # Grupo de Sincronización Bidireccional
        sync_group = QGroupBox("Sincronización Bidireccional de Carpeta")
        sync_layout = QVBoxLayout()
        
        # Ruta Local
        local_layout = QHBoxLayout()
        local_layout.addWidget(QLabel("Ruta Local:"))
        self.local_sync_input = QLineEdit()
        btn_browse_local = QPushButton("Explorar")
        btn_browse_local.clicked.connect(self.browse_local_sync)
        local_layout.addWidget(self.local_sync_input)
        local_layout.addWidget(btn_browse_local)
        sync_layout.addLayout(local_layout)
        
        # Ruta en Drive
        drive_layout = QHBoxLayout()
        drive_layout.addWidget(QLabel("Ruta en Drive:"))
        self.drive_sync_input = QLineEdit()
        drive_layout.addWidget(self.drive_sync_input)
        sync_layout.addLayout(drive_layout)
        
        # Botón Iniciar Sincronización
        self.btn_sync = QPushButton("Iniciar Sincronización")
        self.btn_sync.clicked.connect(self.start_sync)
        sync_layout.addWidget(self.btn_sync)
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        # Checkbox Autostart
        self.checkbox_autostart = QCheckBox("Iniciar automáticamente al encender el equipo")
        self.checkbox_autostart.stateChanged.connect(self.alternar_autostart)
        layout.addWidget(self.checkbox_autostart)
        
        import os
        ruta_autostart = os.path.expanduser("~/.config/autostart/don-juan-drive.desktop")
        if os.path.exists(ruta_autostart):
            self.checkbox_autostart.setChecked(True)
        else:
            self.checkbox_autostart.setChecked(False)
        
        self.remote_input.textChanged.connect(self.reset_status)
        
        btn_save = QPushButton("Guardar Configuración")
        btn_save.clicked.connect(self.save_config)
        layout.addWidget(btn_save)
        
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        
    def reset_status(self):
        self.label_estado.setText("Estado: Sin verificar")
        self.label_estado.setStyleSheet("color: gray; font-weight: bold;")
        
    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio de Montaje")
        if directory:
            self.mount_input.setText(directory)
            
    def browse_local_sync(self):
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio Local")
        if directory:
            self.local_sync_input.setText(directory)
            
    def start_sync(self):
        from PyQt6.QtWidgets import QMessageBox
        local = self.local_sync_input.text().strip()
        remote = self.drive_sync_input.text().strip()
        if not local or not remote:
            QMessageBox.warning(self, "Error", "Ambas rutas son requeridas para la sincronización.")
            return
            
        self.backend.start_bisync(local, remote)
        
        if self.tray_app:
            self.tray_app.show_logs()

    def save_config(self):
        self.backend.remote_name = self.remote_input.text()
        self.backend.mount_path = self.mount_input.text()
        self.backend.cache_size = self.cache_input.text()
        self.hide()
        
    def alternar_autostart(self, state):
        import os
        from PyQt6.QtCore import Qt
        
        ruta_autostart = os.path.expanduser("~/.config/autostart")
        if not os.path.exists(ruta_autostart):
            os.makedirs(ruta_autostart, exist_ok=True)
            
        ruta_archivo = os.path.join(ruta_autostart, "don-juan-drive.desktop")
        
        if state == Qt.CheckState.Checked.value or state == 2:
            ruta_ejecutable = os.path.expanduser("~/.local/bin/don-juan-drive")
            contenido = f"""[Desktop Entry]
Type=Application
Name=Don Juan Drive
Exec={ruta_ejecutable}
Icon=drive_color
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name[es_ES]=Don Juan Drive
"""
            with open(ruta_archivo, "w") as f:
                f.write(contenido)
        else:
            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)

    def run_config(self):
        import shutil
        import subprocess
        from PyQt6.QtCore import QProcess
        
        # Deshabilitar el botón y cambiar su texto
        self.btn_rclone_cfg.setEnabled(False)
        self.btn_rclone_cfg.setText("Abriendo navegador...")
        
        # Limpiar zombis que bloqueen el puerto 53682
        try:
            subprocess.run(["killall", "-9", "rclone"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception:
            pass
        
        current_remote = self.remote_input.text().strip()
        if current_remote.endswith(":"):
            current_remote = current_remote[:-1]
            
        self.navegador_abierto = False
        self.auth_output = ""
        self.login_process = QProcess(self)
        self.login_process.readyReadStandardOutput.connect(self.capturar_url_auth)
        self.login_process.readyReadStandardError.connect(self.capturar_url_auth)
        self.login_process.finished.connect(self.post_login)
        
        rclone_path = shutil.which("rclone") or "rclone"
        
        # Esto iniciará un servidor OAuth local y abrirá el navegador sin emulador de terminal
        self.login_process.start(rclone_path, ["config", "create", current_remote, "drive", "config_is_local", "true"])

    def capturar_url_auth(self):
        import re
        import webbrowser
            
        data_out = self.login_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        data_err = self.login_process.readAllStandardError().data().decode('utf-8', errors='ignore')
        
        if data_out.strip():
            print(f"RCLONE STDOUT DICE: {data_out.strip()}")
        if data_err.strip():
            print(f"RCLONE STDERR DICE: {data_err.strip()}")
            
        self.auth_output += data_out + "\n" + data_err
        
        if self.navegador_abierto:
            return
            
        patron = r"(http://(?:127\.0\.0\.1|localhost):\d+/auth\S+)"
        match = re.search(patron, self.auth_output)
        if match:
            self.navegador_abierto = True
            url = match.group(1)
            print(f">>> ABRIENDO NAVEGADOR: {url}")
            webbrowser.open(url)

    def post_login(self, exitCode, exitStatus):
        from PyQt6.QtWidgets import QMessageBox
        
        # Restaurar botón
        self.btn_rclone_cfg.setEnabled(True)
        self.btn_rclone_cfg.setText("Iniciar Sesión con Google")
        
        if exitCode == 0:
            QMessageBox.information(self, "Éxito", "La cuenta se vinculó correctamente.")
            # Refrescamos la UI y preguntamos si quiere montar (reutiliza el código de verificación)
            self.verificar_nueva_cuenta()
        else:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Inicio de Sesión Fallido")
            msg_box.setText("Se canceló el proceso o hubo un error durante la autenticación.")
            if self.auth_output.strip():
                msg_box.setDetailedText(self.auth_output.strip())
            msg_box.exec()

    def verificar_nueva_cuenta(self):
        import subprocess
        from PyQt6.QtWidgets import QMessageBox
        
        try:
            result = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True, check=True)
            # Limpiamos los espacios en blanco de cada línea por si acaso
            remotes = [r.strip() for r in result.stdout.splitlines() if r.strip()]
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo al intentar verificar los remotos: {str(e)}")
            return
            
        current_remote = self.remote_input.text().strip()
        if current_remote.endswith(":"):
            current_remote = current_remote[:-1]
            
        expected_remote = f"{current_remote}:"
        
        if expected_remote in remotes:
            self.label_estado.setText("Estado: 🟢 Vinculado")
            self.label_estado.setStyleSheet("color: green; font-weight: bold;")
            
            reply = QMessageBox.question(
                self, 
                "Cuenta Vinculada", 
                f"La cuenta '{current_remote}' fue vinculada exitosamente.\n¿Deseas montar la unidad ahora?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.save_config()  # Guardar los cambios
                if self.tray_app:
                    self.tray_app.iniciar_montaje_intencional()
                else:
                    self.backend.start_mount() # Disparar montaje
                self.hide()
        else:
            self.label_estado.setText("Estado: 🔴 No detectado")
            self.label_estado.setStyleSheet("color: red; font-weight: bold;")
            
            QMessageBox.warning(
                self, 
                "Configuración Incompleta", 
                f"No se detectó configuración para '{current_remote}'.\nSi no terminaste el proceso, puedes intentarlo de nuevo."
            )


class DriveTrayApp(QObject):
    def __init__(self, app, backend):
        super().__init__()
        self.app = app
        self.backend = backend
        self.deberia_estar_montado = False
        self.ventana_config = None
        
        # Iniciar monitoreo de red
        self.monitor_red = MonitorRed()
        self.monitor_red.conexion_cambiada.connect(self.procesar_cambio_red)
        self.monitor_red.start()
        
        # Inicializar ventana de logs y conectarla a la señal del backend
        self.log_window = LogWindow()
        self.backend.log_message.connect(self.log_window.append_log)
        
        # Conectar señales del backend
        self.backend.status_changed.connect(self.update_status)
        self.backend.error_occurred.connect(self.show_error)
        
        # Carga de Assets Reales con Fallback Nativo (Rutas absolutas MEIPASS)
        ruta_color = resource_path("drive_color.png")
        ruta_gris = resource_path("drive_gris.png")
        
        self.icono_conectado = QIcon(ruta_color)
        self.icono_desconectado = QIcon(ruta_gris)
        
        if self.icono_conectado.isNull():
            self.icono_conectado = QIcon.fromTheme("cloud-check")
            if self.icono_conectado.isNull():
                self.icono_conectado = QIcon.fromTheme("network-workgroup")
                
        if self.icono_desconectado.isNull():
            self.icono_desconectado = QIcon.fromTheme("cloud-offline")
            if self.icono_desconectado.isNull():
                self.icono_desconectado = QIcon.fromTheme("network-disconnect")
        
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icono_desconectado)
        self.tray.setVisible(True)
        
        # Menú contextual
        self.menu = QMenu()
        
        self.action_status = QAction("Estado: Desconectado", self.menu)
        self.action_status.setEnabled(False)
        self.menu.addAction(self.action_status)
        
        self.menu.addSeparator()
        
        self.action_open = QAction("Abrir carpeta de Drive", self.menu)
        self.action_open.triggered.connect(self.open_drive)
        self.menu.addAction(self.action_open)
        
        self.action_mount = QAction("Conectar", self.menu)
        self.action_mount.triggered.connect(self.iniciar_montaje_intencional)
        self.menu.addAction(self.action_mount)
        
        self.action_refresh = QAction("Refrescar Unidades Compartidas", self.menu)
        self.action_refresh.triggered.connect(self.refrescar_team_drives)
        self.menu.addAction(self.action_refresh)
        
        self.action_unmount = QAction("Desconectar", self.menu)
        self.action_unmount.triggered.connect(self.cierre_intencional)
        self.action_unmount.setVisible(False)
        self.menu.addAction(self.action_unmount)
        
        self.menu.addSeparator()
        
        self.action_login = QAction("Iniciar Sesión con Google", self.menu)
        self.action_login.triggered.connect(self.run_direct_login)
        self.menu.addAction(self.action_login)
        
        self.action_config = QAction("Preferencias", self.menu)
        self.action_config.triggered.connect(self.show_preferences)
        self.menu.addAction(self.action_config)
        
        self.action_logs = QAction("Ver Registros", self.menu)
        self.action_logs.triggered.connect(self.show_logs)
        self.menu.addAction(self.action_logs)
        
        self.action_exit = QAction("Salir", self.menu)
        self.action_exit.triggered.connect(self.exit_app)
        self.menu.addAction(self.action_exit)
        
        self.tray.setContextMenu(self.menu)
        
        # Conectar activación de la bandeja (Clic izquierdo abre Popup oficial)
        self.tray.activated.connect(self.on_tray_activated)
        
        # Inicializar Popup moderno y Ventana de Preferencias Material 3
        from tray_popup import DriveTrayPopup
        from preferences import DrivePreferencesWindow
        self.popup = DriveTrayPopup(self.backend)
        self.preferences_window = DrivePreferencesWindow(self.backend)
        self.popup.open_preferences_requested.connect(self.show_preferences)
        self.popup.open_logs_requested.connect(self.show_logs)
        
        # Conexión global para atrapar apagados del sistema operativo o Ctrl+Q
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().aboutToQuit.connect(self.cierre_seguro)
        
        # Lógica de auto-arranque con retraso inteligente (8 segundos para esperar red)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(8000, self.auto_mount_check)

    def auto_mount_check(self):
        import subprocess
        # Ejecutar silenciosamente para no interrumpir al usuario en ningún momento
        try:
            result = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True, check=True)
            remotes = [r.strip() for r in result.stdout.splitlines() if r.strip()]
        except Exception:
            # Fallback en caso de que rclone crashee por completo
            self.show_config()
            return
            
        current_remote = self.backend.remote_name.strip()
        if current_remote.endswith(":"):
            current_remote = current_remote[:-1]
            
        if f"{current_remote}:" in remotes:
            # Si el remoto está configurado, iniciar montaje automáticamente
            self.iniciar_montaje_intencional()
        else:
            # No hay cuenta, forzamos a mostrar la configuración automáticamente
            self.show_config()
            
    def iniciar_montaje_intencional(self):
        self.deberia_estar_montado = True
        self.backend.start_mount()
        
    def refrescar_team_drives(self):
        from PyQt6.QtCore import QProcess
        import subprocess
        
        # Detener únicamente el montaje de unidades compartidas
        if self.backend.process_team.state() != QProcess.ProcessState.NotRunning:
            if not self.backend.process_team.waitForFinished(2000):
                self.backend.process_team.terminate()
                
        # Forzar desmontaje
        try:
            subprocess.run(['fusermount', '-uz', self.backend.mount_path_team], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception:
            pass
            
        # Reconstruir el remoto combine
        self.backend.has_team_drives = self.backend.preparar_team_drives()
        
        # Reconectar
        if self.backend.has_team_drives:
            args_team = [
                "mount", "gdrive_teamdrives:", self.backend.mount_path_team,
                "--vfs-cache-mode", "full",
                "--vfs-cache-max-size", self.backend.cache_size,
                "--dir-cache-time", "10m",
                "--log-level", "INFO"
            ]
            self.backend.process_team.start("rclone", args_team)
            self.tray.showMessage("Don Juan Drive", "Unidades compartidas actualizadas y listas", QSystemTrayIcon.MessageIcon.Information, 3000)

    def cierre_intencional(self):
        self.deberia_estar_montado = False
        self.backend.cierre_seguro()

    def procesar_cambio_red(self, conectividad):
        try:
            if not self.deberia_estar_montado:
                return
                
            if not conectividad:
                # Perdió la conexión: Limpiar montaje FUSE "zombie"
                self.tray.setIcon(self.icono_desconectado)
                self.backend.cierre_seguro()
            else:
                # Regresó la red: Reconectar
                if not self.backend.is_mounted():
                    self.backend.start_mount()
        except Exception as e:
            print(f"Error procesando cambio de red en GUI thread: {e}")
        
    def update_status(self, is_mounted):
        if is_mounted:
            self.tray.setIcon(self.icono_conectado)
            self.action_status.setText("Estado: Montado")
            self.action_mount.setVisible(False)
            self.action_unmount.setVisible(True)
            self.tray.showMessage("Don Juan Drive", "Don Juan Drive conectado y listo.", QSystemTrayIcon.MessageIcon.Information, 2000)
        else:
            self.tray.setIcon(self.icono_desconectado)
            self.action_status.setText("Estado: Desconectado")
            self.action_mount.setVisible(True)
            self.action_unmount.setVisible(False)
            self.tray.showMessage("Don Juan Drive", "Unidad desconectada.", QSystemTrayIcon.MessageIcon.Information, 2000)

    def show_error(self, message):
        self.tray.showMessage("Error - Don Juan Drive", message, QSystemTrayIcon.MessageIcon.Critical, 5000)
        
    def open_drive(self):
        import os
        import subprocess
        target = self.backend.root_drive_path
        if not os.path.exists(target):
            self.backend.setup_file_explorer_integration()
        if os.path.exists(target):
            subprocess.Popen(["xdg-open", target])
        elif os.path.exists(self.backend.mount_path):
            subprocess.Popen(["xdg-open", self.backend.mount_path])
        else:
            self.show_error("La carpeta de Google Drive no está montada.")
            
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.popup.toggle_popup(self.tray.geometry())

    def show_preferences(self):
        if hasattr(self, 'preferences_window') and self.preferences_window:
            self.preferences_window.show()
            self.preferences_window.raise_()
            self.preferences_window.activateWindow()

    def show_config(self):
        self.show_preferences()

    def run_direct_login(self):
        from account_dialog import GoogleAccountDialog
        dialog = GoogleAccountDialog(self.backend)
        dialog.open_preferences_requested.connect(self.show_preferences)
        dialog.login_requested.connect(self.start_oauth_login)
        dialog.exec()

    def start_oauth_login(self):
        import shutil
        import subprocess
        from PyQt6.QtWidgets import QMessageBox
        rclone_path = shutil.which("rclone") or "rclone"
        try:
            subprocess.Popen([rclone_path, "config", "reconnect", f"{self.backend.remote_name}:"])
        except Exception as e:
            QMessageBox.information(None, "Iniciar Sesión", f"Ejecuta en tu terminal:\nrclone config reconnect {self.backend.remote_name}:")
        
    def show_logs(self):
        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()
        
    def cierre_seguro(self):
        # Desmontar siempre antes de cerrar, sin importar el estado
        self.deberia_estar_montado = False
        self.backend.cierre_seguro()

    def exit_app(self):
        self.cierre_seguro()
        self.app.quit()
