"""
account_dialog.py: Cuadro de diálogo de Cuenta de Google Drive (Material 3).
Muestra el perfil activo, almacenamiento usado, estado de conexión y opciones de autenticación.
"""

import os
import json
import subprocess
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QProgressBar, QMessageBox
)
from PyQt6.QtGui import QIcon, QCursor, QDesktopServices
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QTimer
from PyQt6.QtSvgWidgets import QSvgWidget

from styles import MATERIAL_STYLE

def get_asset(filename):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", filename)


class GoogleAccountDialog(QDialog):
    login_requested = pyqtSignal()
    open_preferences_requested = pyqtSignal()

    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.setWindowTitle("Cuenta de Google Drive")
        self.setFixedSize(400, 380)
        self.setStyleSheet(MATERIAL_STYLE)
        self._init_ui()
        self._load_storage()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)
        
        # Header: Avatar + Nombre
        header_row = QHBoxLayout()
        header_row.setSpacing(14)
        
        avatar_lbl = QLabel("J")
        avatar_lbl.setObjectName("AvatarButton")
        avatar_lbl.setFixedSize(54, 54)
        avatar_lbl.setStyleSheet("""
            background-color: #0B57D0;
            color: #FFFFFF;
            font-size: 22px;
            font-weight: bold;
            border-radius: 27px;
            qproperty-alignment: AlignCenter;
        """)
        header_row.addWidget(avatar_lbl)
        
        user_info = QVBoxLayout()
        user_info.setSpacing(3)
        name_lbl = QLabel("Alimentos SAS & DFC")
        name_lbl.setStyleSheet("font-size: 16px; font-weight: 600; color: #1F1F1F;")
        user_info.addWidget(name_lbl)
        
        remote_lbl = QLabel(f"Remoto activo: {self.backend.remote_name}:")
        remote_lbl.setStyleSheet("font-size: 12px; color: #747775;")
        user_info.addWidget(remote_lbl)
        
        self.status_badge = QLabel("🟢 Conectado y sincronizando" if self.backend.is_mounted() else "⚪ Desconectado / En pausa")
        self.status_badge.setStyleSheet("font-size: 11px; font-weight: 500; color: #146C2E;" if self.backend.is_mounted() else "font-size: 11px; color: #747775;")
        user_info.addWidget(self.status_badge)
        
        header_row.addLayout(user_info, stretch=1)
        layout.addLayout(header_row)
        
        # Tarjeta de Almacenamiento
        storage_card = QFrame()
        storage_card.setProperty("class", "BentoCard")
        s_layout = QVBoxLayout(storage_card)
        s_layout.setContentsMargins(14, 12, 14, 12)
        s_layout.setSpacing(8)
        
        s_title = QLabel("Almacenamiento de Google Workspace")
        s_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #444746;")
        s_layout.addWidget(s_title)
        
        self.storage_text = QLabel("Consultando cuota disponible...")
        self.storage_text.setStyleSheet("font-size: 12px; color: #1F1F1F;")
        s_layout.addWidget(self.storage_text)
        
        self.storage_bar = QProgressBar()
        self.storage_bar.setFixedHeight(8)
        self.storage_bar.setTextVisible(False)
        self.storage_bar.setStyleSheet("""
            QProgressBar { background-color: #E0E2EC; border: none; border-radius: 4px; }
            QProgressBar::chunk { background-color: #0B57D0; border-radius: 4px; }
        """)
        s_layout.addWidget(self.storage_bar)
        layout.addWidget(storage_card)
        
        # Botones de Acción
        layout.addSpacing(6)
        
        btn_manage = QPushButton("🌐  Abrir Drive en el navegador")
        btn_manage.setProperty("class", "PillActionButton")
        btn_manage.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_manage.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://drive.google.com")))
        layout.addWidget(btn_manage)
        
        btn_prefs = QPushButton("⚙️  Preferencias de sincronización")
        btn_prefs.setProperty("class", "PillActionButton")
        btn_prefs.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_prefs.clicked.connect(self._on_prefs)
        layout.addWidget(btn_prefs)
        
        btn_login = QPushButton("🔑  Cambiar / Vincular otra cuenta de Google")
        btn_login.setProperty("class", "PillActionButton")
        btn_login.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_login.clicked.connect(self._on_relogin)
        layout.addWidget(btn_login)
        
        layout.addStretch()
        
        # Botón Cerrar
        btn_close = QPushButton("Cerrar")
        btn_close.setProperty("class", "SecondaryButton")
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def _on_prefs(self):
        self.accept()
        self.open_preferences_requested.emit()

    def _on_relogin(self):
        self.accept()
        self.login_requested.emit()

    def _load_storage(self):
        QTimer.singleShot(50, self._fetch_storage)

    def _fetch_storage(self):
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
                        self.storage_text.setText(f"{used_gb/1024:.2f} TB de {total_gb/1024:.1f} TB usados ({percent}%)")
                    else:
                        self.storage_text.setText(f"{used_gb:.1f} GB de {total_gb:.1f} GB usados ({percent}%)")
        except Exception:
            self.storage_text.setText("Cuenta corporativa activa")
