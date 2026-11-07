import os
from PyQt6.QtCore import QObject, pyqtSignal, QProcess

class DriveBackend(QObject):
    status_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    log_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.process_main = QProcess(self)
        self.process_shared = QProcess(self)
        self.process_team = QProcess(self)
        self.bisync_process = QProcess(self)
        
        for proc in [self.process_main, self.process_shared, self.process_team, self.bisync_process]:
            proc.readyReadStandardOutput.connect(lambda p=proc: self.actualizar_logs_stdout(p))
            proc.readyReadStandardError.connect(lambda p=proc: self.actualizar_logs_stderr(p))
            
        for proc in [self.process_main, self.process_shared, self.process_team]:
            proc.finished.connect(self.on_process_finished)
            proc.errorOccurred.connect(self.on_process_error)
            
        self.bisync_process.finished.connect(self.on_bisync_finished)
        
        self.root_drive_path = os.path.expanduser("~/Google Drive")
        self.mount_path = os.path.expanduser("~/GoogleDrive_Mi_Unidad")
        self.mount_path_shared = os.path.expanduser("~/GoogleDrive_Compartido_Conmigo")
        self.mount_path_team = os.path.expanduser("~/GoogleDrive_Unidades_Compartidas")
        
        self.remote_name = "gdrive" # Default rclone remote name
        self.cache_size = "50G"
        self._is_mounted = False
        self.has_team_drives = False
        self._was_mounted_before_sleep = False
        self._setup_sleep_listener()

    def actualizar_logs_stdout(self, process):
        data = process.readAllStandardOutput().data().decode('utf-8')
        if data:
            self.log_message.emit(data.strip())

    def actualizar_logs_stderr(self, process):
        data = process.readAllStandardError().data().decode('utf-8')
        if data:
            self.log_message.emit(data.strip())
            
    def on_process_error(self, error):
        self.error_occurred.emit(f"Error interno en rclone: {error}")
        if self._is_mounted:
            self._is_mounted = False
            self.status_changed.emit(False)

    def on_process_finished(self, exitCode, exitStatus):
        if self._is_mounted:
            self._is_mounted = False
            self.status_changed.emit(False)
            
        if exitCode != 0 and exitCode is not None:
            self.error_occurred.emit(f"rclone terminó inesperadamente (código {exitCode}).")
            
    def on_bisync_finished(self, exitCode, exitStatus):
        if exitCode == 0:
            self.log_message.emit(">>> Sincronización finalizada exitosamente.")
        else:
            self.error_occurred.emit(f"Sincronización falló con código {exitCode}")

    def is_mounted(self):
        return self._is_mounted
        
    def preparar_team_drives(self):
        import subprocess
        import json
        import re
        try:
            result = subprocess.run(['rclone', 'backend', 'drives', f"{self.remote_name}:"], capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout.strip():
                return False
                
            drives = json.loads(result.stdout)
            if not drives:
                return False
                
            upstreams = []
            for drive in drives:
                name = drive.get("name", "")
                drive_id = drive.get("id", "")
                if not name or not drive_id:
                    continue
                clean_name = re.sub(r'\s+', '_', name)
                upstreams.append(f"{clean_name}={self.remote_name},team_drive={drive_id}:")
                
            if upstreams:
                upstreams_str = " ".join(upstreams)
                subprocess.run(['rclone', 'config', 'create', 'gdrive_teamdrives', 'combine', f'upstreams={upstreams_str}'], check=True, stderr=subprocess.DEVNULL)
                return True
            return False
        except Exception as e:
            self.error_occurred.emit(f"Error preparando Team Drives: {e}")
            return False

    def start_mount(self):
        if self._is_mounted:
            return
            
        import subprocess
        # Validación Estricta antes de disparar el QProcess
        try:
            result = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True)
            remotes = [r.strip() for r in result.stdout.splitlines() if r.strip()]
            if f"{self.remote_name}:" not in remotes:
                self.error_occurred.emit(f"Fallo crítico: No se encontró la configuración para '{self.remote_name}:'")
                return
        except Exception as e:
            self.error_occurred.emit(f"Error al verificar remotos de rclone: {e}")
            return

        # Preparar Team Drives
        self.has_team_drives = self.preparar_team_drives()

        paths_to_mount = [self.mount_path, self.mount_path_shared]
        if self.has_team_drives:
            paths_to_mount.append(self.mount_path_team)

        for path in paths_to_mount:
            try:
                subprocess.run(["fusermount", "-uz", path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            except Exception:
                try:
                    subprocess.run(["fusermount3", "-uz", path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                except Exception:
                    pass
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except Exception as e:
                    self.error_occurred.emit(f"No se pudo crear directorio {path}: {e}")
                    return

        args_main = [
            "mount", f"{self.remote_name}:", self.mount_path,
            "--vfs-cache-mode", "full",
            "--vfs-cache-max-size", self.cache_size,
            "--dir-cache-time", "10m",
            "--log-level", "INFO"
        ]
        
        args_shared = [
            "mount", f"{self.remote_name}:", self.mount_path_shared,
            "--drive-shared-with-me",
            "--vfs-cache-mode", "full",
            "--vfs-cache-max-size", self.cache_size,
            "--dir-cache-time", "10m",
            "--log-level", "INFO"
        ]
        
        args_team = [
            "mount", "gdrive_teamdrives:", self.mount_path_team,
            "--vfs-cache-mode", "full",
            "--vfs-cache-max-size", self.cache_size,
            "--dir-cache-time", "10m",
            "--log-level", "INFO"
        ]
        
        try:
            self.process_main.start("rclone", args_main)
            self.process_shared.start("rclone", args_shared)
            
            if self.has_team_drives:
                self.process_team.start("rclone", args_team)
            
            if not self.process_main.waitForStarted(2000) or not self.process_shared.waitForStarted(2000):
                self.error_occurred.emit("Fallo al ejecutar instancias de rclone.")
                return
                
            if self.has_team_drives and not self.process_team.waitForStarted(2000):
                self.error_occurred.emit("Fallo al iniciar el montaje de Team Drives.")
                return
                
            self._is_mounted = True
            self.setup_file_explorer_integration()
            self.status_changed.emit(True)

        except Exception as e:
            self.error_occurred.emit(f"Fallo al ejecutar rclone: {str(e)}")
            self._is_mounted = False

    def setup_file_explorer_integration(self):
        try:
            os.makedirs(self.root_drive_path, exist_ok=True)
            links = [
                ("Mi unidad", self.mount_path),
                ("Compartido conmigo", self.mount_path_shared),
                ("Unidades compartidas", self.mount_path_team)
            ]
            for link_name, target in links:
                link_path = os.path.join(self.root_drive_path, link_name)
                try:
                    if os.path.islink(link_path) or os.path.exists(link_path):
                        os.remove(link_path)
                    os.symlink(target, link_path)
                except Exception:
                    pass
            dot_dir = os.path.join(self.root_drive_path, ".directory")
            with open(dot_dir, "w", encoding="utf-8") as f:
                f.write("[Desktop Entry]\nIcon=google-drive\n")
        except Exception as e:
            self.log_message.emit(f"Aviso integración explorador: {e}")

    def cierre_seguro(self):
        # 1. Desmontaje seguro en Linux (provoca que rclone vacíe caché y termine)
        import subprocess
        paths_to_unmount = [self.mount_path, self.mount_path_shared, self.mount_path_team]
        for path in paths_to_unmount:
            try:
                subprocess.run(["fusermount", "-uz", path], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            except Exception:
                try:
                    subprocess.run(["fusermount3", "-uz", path], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                except Exception:
                    pass # Silencioso por si ya estaba desmontado o falló
                
        # 2. Terminación controlada y forzada (Graceful Shutdown)
        for proc in [self.process_main, self.process_shared, self.process_team]:
            if proc.state() != QProcess.ProcessState.NotRunning:
                if not proc.waitForFinished(3000):
                    proc.kill()
            
        self._is_mounted = False
        self.status_changed.emit(False)

    def _setup_sleep_listener(self):
        try:
            from PyQt6.QtDBus import QDBusConnection
            system_bus = QDBusConnection.systemBus()
            connected = system_bus.connect(
                "org.freedesktop.login1",
                "/org/freedesktop/login1",
                "org.freedesktop.login1.Manager",
                "PrepareForSleep",
                self._on_prepare_for_sleep
            )
            if connected:
                self.log_message.emit(">>> Monitoreo de suspensión del sistema (systemd PrepareForSleep) activado.")
        except Exception as e:
            self.log_message.emit(f"Aviso: No se pudo enlazar con systemd PrepareForSleep: {e}")

    def _on_prepare_for_sleep(self, sleeping: bool):
        if sleeping:
            if self._is_mounted:
                self._was_mounted_before_sleep = True
                self.log_message.emit(">>> Suspensión detectada: Desmontando unidades para evitar bloqueos del sistema...")
                self.cierre_seguro()
        else:
            if self._was_mounted_before_sleep:
                self._was_mounted_before_sleep = False
                self.log_message.emit(">>> Reanudación detectada: Remontando unidades Google Drive...")
                self.start_mount()
        
    def start_bisync(self, local_path, remote_path):
        if self.bisync_process.state() != QProcess.ProcessState.NotRunning:
            self.error_occurred.emit("Ya hay una sincronización en curso.")
            return
            
        args = [
            "bisync", local_path, f"{self.remote_name}:{remote_path}",
            "--resync", "--verbose"
        ]
        
        self.log_message.emit(">>> Iniciando sincronización bidireccional...")
        self.bisync_process.start("rclone", args)
