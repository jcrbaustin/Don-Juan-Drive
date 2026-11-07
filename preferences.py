"""
preferences.py: Ventana de Preferencias de Google Drive (Material 3).
Réplica de la ventana de configuración oficial con pestañas funcionales (My Computer y Google Drive),
selector de Stream vs Mirror y medidor de cuota en vivo.
"""

import os
import json
import subprocess
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QFrame,
    QProgressBar, QStackedWidget, QFileDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QIcon, QCursor, QDesktopServices
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QUrl, QTimer
from PyQt6.QtSvgWidgets import QSvgWidget

from styles import MATERIAL_STYLE

def get_asset(filename):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", filename)


class DrivePreferencesWindow(QDialog):
    preferences_saved = pyqtSignal(dict)

    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.setWindowTitle("Google Drive Preferences")
        self.setObjectName("PreferencesWindow")
        self.setFixedSize(760, 560)
        self.setStyleSheet(MATERIAL_STYLE)
        
        self.current_sync_mode = "stream"
        self._init_ui()
        self._load_account_storage()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Barra lateral izquierda
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar, stretch=0)
        
        # 2. Stacked widget para las páginas
        self.pages_stack = QStackedWidget()
        
        self.page_computer = self._create_my_computer_panel()
        self.page_drive = self._create_drive_panel()
        
        self.pages_stack.addWidget(self.page_computer)  # Index 0
        self.pages_stack.addWidget(self.page_drive)     # Index 1
        self.pages_stack.setCurrentIndex(1)             # Por defecto Google Drive
        
        main_layout.addWidget(self.pages_stack, stretch=1)

    def _create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("PreferencesSidebar")
        sidebar.setFixedWidth(240)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(6)
        
        # Logo Drive en sidebar
        logo_row = QHBoxLayout()
        logo_svg = QSvgWidget(get_asset("logo_drive_no_border.svg"))
        logo_svg.setFixedSize(28, 28)
        logo_row.addWidget(logo_svg)
        
        brand_lbl = QLabel("Google Drive")
        brand_lbl.setStyleSheet("font-size: 16px; font-weight: 600; color: #1F1F1F;")
        logo_row.addWidget(brand_lbl)
        logo_row.addStretch()
        layout.addLayout(logo_row)
        
        layout.addSpacing(20)
        
        # Pestaña 1: My Computer
        self.btn_tab_computer = QPushButton("My Computer\nFolders from your computer")
        self.btn_tab_computer.setProperty("class", "DrawerTab")
        self.btn_tab_computer.setStyleSheet("text-align: left; padding: 10px 14px; border-radius: 12px;")
        self.btn_tab_computer.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_computer.clicked.connect(lambda: self._switch_tab(0))
        layout.addWidget(self.btn_tab_computer)
        
        # Pestaña 2: Google Drive (Seleccionada)
        self.btn_tab_drive = QPushButton("Google Drive\nFolders from Drive")
        self.btn_tab_drive.setProperty("class", "DrawerTab")
        self.btn_tab_drive.setProperty("selected", "true")
        self.btn_tab_drive.setStyleSheet("text-align: left; padding: 10px 14px; border-radius: 12px;")
        self.btn_tab_drive.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_drive.clicked.connect(lambda: self._switch_tab(1))
        layout.addWidget(self.btn_tab_drive)
        
        layout.addStretch()
        
        # Cuota de almacenamiento
        self.storage_label = QLabel("Calculando espacio...")
        self.storage_label.setStyleSheet("font-size: 11px; color: #444746;")
        layout.addWidget(self.storage_label)
        
        self.storage_bar = QProgressBar()
        self.storage_bar.setFixedHeight(6)
        self.storage_bar.setTextVisible(False)
        self.storage_bar.setStyleSheet("""
            QProgressBar { background-color: #E0E2EC; border: none; border-radius: 3px; }
            QProgressBar::chunk { background-color: #0B57D0; border-radius: 3px; }
        """)
        layout.addWidget(self.storage_bar)
        layout.addSpacing(10)
        
        return sidebar

    def _create_my_computer_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)
        
        title = QLabel("My Computer")
        title.setProperty("class", "PrefSectionTitle")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(title)
        
        sub = QLabel("Sync folders from your computer with Google Drive.")
        sub.setProperty("class", "PrefSubtitle")
        layout.addWidget(sub)
        
        # Botón para añadir carpeta
        btn_add_folder = QPushButton("+  Add folder to sync")
        btn_add_folder.setProperty("class", "SecondaryButton")
        btn_add_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_add_folder.clicked.connect(self._add_computer_folder)
        btn_add_folder.setFixedWidth(200)
        layout.addWidget(btn_add_folder)
        
        # Lista de carpetas configuradas
        layout.addSpacing(6)
        lbl_list = QLabel("Configured local folders:")
        lbl_list.setStyleSheet("font-weight: 500; font-size: 13px; color: #1F1F1F;")
        layout.addWidget(lbl_list)
        
        self.local_folders_list = QListWidget()
        self.local_folders_list.setStyleSheet("""
            QListWidget { background: #F8FAFD; border: 1px solid #E0E2EC; border-radius: 10px; padding: 6px; }
            QListWidget::item { padding: 8px; border-radius: 6px; }
            QListWidget::item:hover { background: #E9EEF6; }
        """)
        self._load_default_synced_folders()
        layout.addWidget(self.local_folders_list, stretch=1)
        
        # Botones inferiores
        btn_row = self._create_bottom_buttons()
        layout.addLayout(btn_row)
        return panel

    def _load_default_synced_folders(self):
        self.local_folders_list.clear()
        default_folders = [
            ("📁 " + os.path.expanduser("~/Google Drive/Mi unidad"), "Sincronización en la nube (FUSE Stream)"),
            ("📁 " + os.path.expanduser("~/Google Drive/Compartido conmigo"), "Archivos compartidos"),
            ("📁 " + os.path.expanduser("~/Google Drive/Unidades compartidas"), "Unidades de equipo / Team Drives")
        ]
        for path, desc in default_folders:
            item = QListWidgetItem(f"{path}\n   ↳ {desc}")
            self.local_folders_list.addItem(item)

    def _add_computer_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta local para sincronizar con Google Drive")
        if folder:
            name = os.path.basename(folder)
            self.backend.start_bisync(folder, name)
            item = QListWidgetItem(f"📁 {folder}\n   ↳ Sincronización bidireccional activa")
            self.local_folders_list.addItem(item)

    def _create_drive_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)
        
        title = QLabel("Google Drive")
        title.setProperty("class", "PrefSectionTitle")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(title)
        
        sub = QLabel("Browse and open Google Drive from your computer.")
        sub.setProperty("class", "PrefSubtitle")
        layout.addWidget(sub)
        
        btn_open = QPushButton("Open in File Explorer")
        btn_open.setProperty("class", "SecondaryButton")
        btn_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_open.clicked.connect(self._open_in_file_explorer)
        btn_open.setFixedWidth(190)
        layout.addWidget(btn_open)
        
        layout.addSpacing(6)
        
        opts_title = QLabel("My Drive syncing options")
        opts_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1F1F1F;")
        layout.addWidget(opts_title)
        
        self.radio_group = QButtonGroup(self)
        
        # Stream files
        self.radio_stream = QRadioButton("Stream files")
        self.radio_stream.setChecked(True)
        self.radio_group.addButton(self.radio_stream)
        layout.addWidget(self.radio_stream)
        
        stream_desc = QLabel(
            "   ✓ Store all My Drive files in the cloud only\n"
            "   ✓ Access files from a virtual drive or folder on your computer\n"
            "   ✓ Choose specific files and folders to make available offline."
        )
        stream_desc.setStyleSheet("color: #444746; font-size: 12px; margin-left: 18px; line-height: 1.5;")
        layout.addWidget(stream_desc)
        
        layout.addSpacing(6)
        
        # Mirror files
        self.radio_mirror = QRadioButton("Mirror files")
        self.radio_group.addButton(self.radio_mirror)
        layout.addWidget(self.radio_mirror)
        
        mirror_desc = QLabel(
            "   ✓ Store all My Drive files in the cloud and on your computer\n"
            "   ✓ Access files from a folder on your computer\n"
            "   ✓ All files are automatically available offline"
        )
        mirror_desc.setStyleSheet("color: #444746; font-size: 12px; margin-left: 18px; line-height: 1.5;")
        layout.addWidget(mirror_desc)
        
        layout.addSpacing(6)
        
        # Banner azul de información
        info_banner = QFrame()
        info_banner.setObjectName("InfoBanner")
        info_layout = QHBoxLayout(info_banner)
        info_layout.setContentsMargins(12, 10, 12, 10)
        
        info_text = QLabel(
            "ℹ  Streaming uses less hard drive space. Only use hard drive space when you "
            "open files or make files available offline."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #041E49; font-size: 12px;")
        info_layout.addWidget(info_text)
        layout.addWidget(info_banner)
        
        layout.addStretch()
        
        btn_row = self._create_bottom_buttons()
        layout.addLayout(btn_row)
        return panel

    def _create_bottom_buttons(self):
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "SecondaryButton")
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        
        btn_save = QPushButton("Save")
        btn_save.setProperty("class", "PrimaryButton")
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.clicked.connect(self._save_preferences)
        btn_row.addWidget(btn_save)
        
        return btn_row

    def _switch_tab(self, index):
        self.pages_stack.setCurrentIndex(index)
        if index == 0:
            self.btn_tab_computer.setProperty("selected", "true")
            self.btn_tab_drive.setProperty("selected", "false")
        else:
            self.btn_tab_computer.setProperty("selected", "false")
            self.btn_tab_drive.setProperty("selected", "true")
        self.btn_tab_computer.style().unpolish(self.btn_tab_computer)
        self.btn_tab_computer.style().polish(self.btn_tab_computer)
        self.btn_tab_drive.style().unpolish(self.btn_tab_drive)
        self.btn_tab_drive.style().polish(self.btn_tab_drive)

    def run_config(self):
        import subprocess
        try:
            subprocess.Popen(["rclone", "config", "reconnect", f"{self.backend.remote_name}:"])
        except Exception:
            pass

    def _open_in_file_explorer(self):
        path = self.backend.root_drive_path
        if not os.path.exists(path):
            self.backend.setup_file_explorer_integration()
        subprocess.Popen(["xdg-open", path])

    def _save_preferences(self):
        mode = "stream" if self.radio_stream.isChecked() else "mirror"
        self.current_sync_mode = mode
        
        if mode == "stream":
            if not self.backend.is_mounted():
                self.backend.start_mount()
        else:
            local_folder = self.backend.mount_path
            self.backend.start_bisync(local_folder, "")
            
        self.preferences_saved.emit({"sync_mode": mode})
        self.accept()

    def _load_account_storage(self):
        QTimer.singleShot(100, self._fetch_storage_async)

    def _fetch_storage_async(self):
        try:
            res = subprocess.run(["rclone", "about", f"{self.backend.remote_name}:", "--json"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                total = data.get("total", 0)
                used = data.get("used", 0)
                if total > 0:
                    percent = int((used / total) * 100)
                    self.storage_bar.setValue(percent)
                    used_gb = used / (1024**3)
                    total_gb = total / (1024**3)
                    if total_gb >= 1024:
                        self.storage_label.setText(f"{used_gb/1024:.1f} TB de {total_gb/1024:.1f} TB usados")
                    else:
                        self.storage_label.setText(f"{used_gb:.1f} GB de {total_gb:.1f} GB usados")
        except Exception:
            self.storage_label.setText("Google Drive Conectado")
