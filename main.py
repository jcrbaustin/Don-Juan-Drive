import sys
import shutil
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from gui import DriveTrayApp

def manejador_excepciones(tipo, valor, tb):
    error = "".join(traceback.format_exception(tipo, valor, tb))
    print(f"ERROR CRÍTICO CAPTURADO:\n{error}")
    # Guarda el log en la ruta actual donde se ejecutó el binario (ej. home directory)
    with open("crash_drive.log", "w") as f:
        f.write(error)

sys.excepthook = manejador_excepciones

def check_dependencies():
    missing = []
    if not shutil.which("rclone"):
        missing.append("rclone")
    
    # Comprobar si existe fusermount o fusermount3 (KDE/Fedora moderno)
    if not shutil.which("fusermount") and not shutil.which("fusermount3"):
        missing.append("fuse")
        
    return missing

def main():
    app = QApplication(sys.argv)
    
    # Mantener la aplicación viva en background incluso si se cierran diálogos
    app.setQuitOnLastWindowClosed(False)

    # Validar dependencias (Paso 1)
    missing = check_dependencies()
    if missing:
        QMessageBox.critical(
            None, 
            "Dependencias Faltantes", 
            f"Faltan herramientas esenciales en el sistema: {', '.join(missing)}\n\n"
            "Por favor, instala los requerimientos abriendo la terminal y ejecutando:\n\n"
            "sudo dnf install rclone fuse"
        )
        sys.exit(1)

    # Iniciar el backend primero
    from backend import DriveBackend
    backend = DriveBackend()

    # Iniciar la aplicación en el System Tray
    tray_app = DriveTrayApp(app, backend)
    
    # Iniciar Ventana Principal (Configuración) de inmediato
    from gui import ConfigWindow
    ventana = ConfigWindow(backend, tray_app)
    tray_app.ventana_config = ventana
    
    import subprocess
    result = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True)
    remotes = [r.strip() for r in result.stdout.splitlines() if r.strip()]
    
    if "gdrive:" not in remotes:
        # Mostrar la ventana y forzar ciclo de vida
        ventana.show()
    else:
        # Iniciar silenciosamente el montaje de las unidades
        tray_app.iniciar_montaje_intencional()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
