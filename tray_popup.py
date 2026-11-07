"""
tray_popup.py: Ventana emergente tipo Pop-up anclada al System Tray de Google Drive.
Material 3 / Google Workspace Desktop idéntica a la versión oficial.
Incluye pestañas interactivas (Home, Sync activity, Notifications), Bento Grid y apertura directa en Dolphin.
"""

import os
import glob
import time
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QToolButton, QGridLayout, QFrame, QScrollArea,
    QFileDialog, QGraphicsDropShadowEffect, QStackedWidget
)
from PyQt6.QtGui import QIcon, QColor, QCursor, QDesktopServices
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QUrl
from PyQt6.QtSvgWidgets import QSvgWidget

from styles import MATERIAL_STYLE

def get_asset(filename):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", filename)


class DriveTrayPopup(QWidget):
    open_preferences_requested = pyqtSignal()
    open_logs_requested = pyqtSignal()
    sync_toggled = pyqtSignal()

    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.setObjectName("DrivePopup")
        
        # Flags para popup sin bordes con comportamiento nativo
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.setStyleSheet(MATERIAL_STYLE)
        self.setFixedSize(760, 530)
        
        # Sombra sutil
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        container = QFrame(self)
        container.setObjectName("DrivePopup")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 1. Header superior
        header = self._create_header()
        container_layout.addWidget(header)
        
        # 2. Cuerpo: Drawer izquierdo + Vistas en StackedWidget
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 16, 16)
        body_layout.setSpacing(16)
        
        drawer = self._create_drawer()
        body_layout.addWidget(drawer, stretch=0)
        
        # Vistas intercambiables
        self.stacked_views = QStackedWidget()
        
        self.view_home = self._create_bento_grid()
        self.view_activity = self._create_activity_view()
        self.view_notifications = self._create_notifications_view()
        
        self.stacked_views.addWidget(self.view_home)         # Index 0
        self.stacked_views.addWidget(self.view_activity)     # Index 1
        self.stacked_views.addWidget(self.view_notifications)# Index 2
        
        body_layout.addWidget(self.stacked_views, stretch=1)
        container_layout.addWidget(body)
        main_layout.addWidget(container)

    def _create_header(self):
        header_widget = QWidget()
        header_widget.setObjectName("HeaderContainer")
        layout = QHBoxLayout(header_widget)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(12)
        
        # Logo Drive + Título
        logo_svg = QSvgWidget(get_asset("logo_drive_no_border.svg"))
        logo_svg.setFixedSize(26, 26)
        layout.addWidget(logo_svg)
        
        title_label = QLabel("Drive")
        title_label.setObjectName("AppTitle")
        layout.addWidget(title_label)
        
        layout.addSpacing(16)
        
        # Barra de búsqueda funcional
        search_box = QWidget()
        search_layout = QHBoxLayout(search_box)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchBar")
        self.search_input.setPlaceholderText("Search in Drive")
        self.search_input.setMinimumWidth(260)
        self.search_input.returnPressed.connect(self._on_search)
        
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_box, stretch=1)
        
        # Botón Pausar / Reanudar sincronización
        self.pause_btn = QToolButton()
        self.pause_btn.setIcon(QIcon(get_asset("ic_pause_circle_outline_grey600_24px.svg")))
        self.pause_btn.setIconSize(QSize(22, 22))
        self.pause_btn.setToolTip("Pausar sincronización")
        self.pause_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pause_btn.clicked.connect(self._toggle_pause_sync)
        layout.addWidget(self.pause_btn)
        
        # Botón Configuración / Preferencias
        settings_btn = QToolButton()
        settings_btn.setIcon(QIcon(get_asset("ic_settings_grey_24dp.svg")))
        settings_btn.setIconSize(QSize(22, 22))
        settings_btn.setToolTip("Preferencias")
        settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        settings_btn.clicked.connect(self._open_preferences)
        layout.addWidget(settings_btn)
        
        # Avatar de usuario
        self.avatar_btn = QPushButton("J")
        self.avatar_btn.setObjectName("AvatarButton")
        self.avatar_btn.setToolTip("Cuenta: Alimentos SAS (gdrive)\nClic para ver detalles de la cuenta")
        self.avatar_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.avatar_btn.clicked.connect(self._show_account_dialog)
        layout.addWidget(self.avatar_btn)
        
        return header_widget

    def _create_drawer(self):
        drawer = QWidget()
        drawer.setObjectName("DrawerContainer")
        layout = QVBoxLayout(drawer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Botón principal: Abrir carpeta de Google Drive en Dolphin
        open_folder_btn = QPushButton("  Open Drive folder")
        open_folder_btn.setObjectName("OpenDriveFolderBtn")
        open_folder_btn.setIcon(QIcon(get_asset("folder_mydrive_24px.svg")))
        open_folder_btn.setIconSize(QSize(18, 18))
        open_folder_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_folder_btn.clicked.connect(self._open_drive_folder)
        layout.addWidget(open_folder_btn)
        
        layout.addSpacing(10)
        
        # Pestañas verticales intercambiables
        self.tab_home = QPushButton("  Home")
        self.tab_home.setProperty("class", "DrawerTab")
        self.tab_home.setProperty("selected", "true")
        self.tab_home.setIcon(QIcon(get_asset("folder_mydrive_24px.svg")))
        self.tab_home.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tab_home.clicked.connect(lambda: self._switch_tab(0))
        layout.addWidget(self.tab_home)
        
        self.tab_activity = QPushButton("  Sync activity")
        self.tab_activity.setProperty("class", "DrawerTab")
        self.tab_activity.setIcon(QIcon(get_asset("ic_sync_grey_24px.svg")))
        self.tab_activity.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tab_activity.clicked.connect(lambda: self._switch_tab(1))
        layout.addWidget(self.tab_activity)
        
        self.tab_notifications = QPushButton("  Notifications")
        self.tab_notifications.setProperty("class", "DrawerTab")
        self.tab_notifications.setIcon(QIcon(get_asset("ic_notification_bell.svg")))
        self.tab_notifications.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tab_notifications.clicked.connect(lambda: self._switch_tab(2))
        layout.addWidget(self.tab_notifications)
        
        layout.addStretch()
        return drawer

    def _switch_tab(self, index):
        self.stacked_views.setCurrentIndex(index)
        self.tab_home.setProperty("selected", "true" if index == 0 else "false")
        self.tab_activity.setProperty("selected", "true" if index == 1 else "false")
        self.tab_notifications.setProperty("selected", "true" if index == 2 else "false")
        
        for tab in [self.tab_home, self.tab_activity, self.tab_notifications]:
            tab.style().unpolish(tab)
            tab.style().polish(tab)
            
        if index == 1:
            self._refresh_activity_list()

    def _create_bento_grid(self):
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(14)
        
        # Card 1: Sync Status (Perro en nube con checkmark)
        self.card_sync = self._build_card(
            title="Sync status",
            subtitle="Your files are up to date",
            caption="Activities on your files and folder will show up here",
            svg_asset="up_to_date.svg",
            svg_size=(90, 85),
            action_button_text="View activity",
            action_callback=lambda: self._switch_tab(1)
        )
        grid.addWidget(self.card_sync, 0, 0)
        
        # Card 2: Caught Up (Chica con margarita)
        card_caught_up = self._build_card(
            title="You're all caught up!",
            subtitle="Things that need your attention will show up here",
            caption="",
            svg_asset="caught_up.svg",
            svg_size=(85, 96)
        )
        grid.addWidget(card_caught_up, 0, 1)
        
        # Card 3: Shared with you (Chica con carpetas)
        card_shared = self._build_card(
            title="View files shared with you",
            subtitle="Stay updated on files people share on Drive web",
            caption="",
            svg_asset="shared_with_you.svg",
            svg_size=(95, 86),
            action_button_text="View all",
            action_callback=self._open_shared_drive
        )
        grid.addWidget(card_shared, 1, 0)
        
        # Card 4: Quick links
        card_links = self._build_quick_links_card()
        grid.addWidget(card_links, 1, 1)
        
        return grid_widget

    def _create_activity_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)
        
        header_row = QHBoxLayout()
        title = QLabel("Sync activity")
        title.setProperty("class", "CardTitle")
        title.setStyleSheet("font-size: 16px;")
        header_row.addWidget(title)
        
        btn_refresh = QPushButton("↻  Refresh")
        btn_refresh.setProperty("class", "PillActionButton")
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.clicked.connect(self._refresh_activity_list)
        header_row.addWidget(btn_refresh, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header_row)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.activity_container = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_container)
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(8)
        
        scroll.setWidget(self.activity_container)
        layout.addWidget(scroll)
        return widget

    def _refresh_activity_list(self):
        # Limpiar lista anterior
        while self.activity_layout.count():
            item = self.activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Obtener archivos modificados recientemente en la unidad montada
        target_dir = self.backend.mount_path
        if not os.path.exists(target_dir):
            target_dir = self.backend.root_drive_path
            
        found_files = []
        try:
            for root, dirs, files in os.walk(target_dir):
                for f in files:
                    if f.startswith("."):
                        continue
                    full_p = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(full_p)
                        found_files.append((mtime, full_p, f))
                    except OSError:
                        pass
                if len(found_files) > 40:
                    break
        except Exception:
            pass
            
        found_files.sort(reverse=True)
        
        if not found_files:
            empty_lbl = QLabel("No hay cambios recientes. Todos los archivos están al día.")
            empty_lbl.setStyleSheet("color: #747775; font-size: 13px; padding: 20px;")
            self.activity_layout.addWidget(empty_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            for mtime, full_p, fname in found_files[:15]:
                card = QFrame()
                card.setProperty("class", "ActivityCard")
                row = QHBoxLayout(card)
                row.setContentsMargins(10, 8, 10, 8)
                row.setSpacing(12)
                
                # Icono
                icon_lbl = QLabel("📄")
                icon_lbl.setStyleSheet("font-size: 18px;")
                row.addWidget(icon_lbl)
                
                # Textos
                col = QVBoxLayout()
                col.setSpacing(2)
                lbl_name = QLabel(fname)
                lbl_name.setProperty("class", "ActivityFileName")
                col.addWidget(lbl_name)
                
                diff_min = int((time.time() - mtime) / 60)
                if diff_min < 1:
                    time_str = "Sincronizado ahora mismo"
                elif diff_min < 60:
                    time_str = f"Sincronizado hace {diff_min} min"
                else:
                    time_str = f"Modificado hoy"
                lbl_meta = QLabel(time_str)
                lbl_meta.setProperty("class", "ActivityMeta")
                col.addWidget(lbl_meta)
                row.addLayout(col, stretch=1)
                
                # Botón Abrir
                btn_open_file = QPushButton("Open")
                btn_open_file.setProperty("class", "PillActionButton")
                btn_open_file.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_open_file.clicked.connect(lambda checked, p=full_p: subprocess.Popen(["xdg-open", p]))
                row.addWidget(btn_open_file)
                
                self.activity_layout.addWidget(card)
                
        self.activity_layout.addStretch()

    def _create_notifications_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        svg_w = QSvgWidget(get_asset("caught_up.svg"))
        svg_w.setFixedSize(120, 130)
        layout.addWidget(svg_w, alignment=Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("You're all caught up!")
        title.setProperty("class", "CardTitle")
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel("Things that need your attention will show up here.\nNo sync conflicts or errors detected.")
        desc.setProperty("class", "CardSubtitle")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        return widget

    def _build_card(self, title, subtitle, caption, svg_asset, svg_size=(80, 80), action_button_text=None, action_callback=None):
        card = QFrame()
        card.setProperty("class", "BentoCard")
        
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)
        
        left_col = QVBoxLayout()
        left_col.setSpacing(6)
        
        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "CardTitle")
        left_col.addWidget(lbl_title)
        
        lbl_sub = QLabel(subtitle)
        lbl_sub.setProperty("class", "CardSubtitle")
        lbl_sub.setWordWrap(True)
        left_col.addWidget(lbl_sub)
        
        if caption:
            lbl_cap = QLabel(caption)
            lbl_cap.setProperty("class", "CardSubtitle")
            lbl_cap.setStyleSheet("color: #747775; font-size: 11px;")
            lbl_cap.setWordWrap(True)
            left_col.addWidget(lbl_cap)
            
        if action_button_text and action_callback:
            left_col.addSpacing(6)
            btn = QPushButton(action_button_text)
            btn.setProperty("class", "PillActionButton")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(action_callback)
            left_col.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)
            
        left_col.addStretch()
        card_layout.addLayout(left_col, stretch=1)
        
        if svg_asset:
            asset_path = get_asset(svg_asset)
            if os.path.exists(asset_path):
                svg_w = QSvgWidget(asset_path)
                svg_w.setFixedSize(svg_size[0], svg_size[1])
                card_layout.addWidget(svg_w, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
                
        return card

    def _build_quick_links_card(self):
        card = QFrame()
        card.setProperty("class", "BentoCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        
        title = QLabel("Quick links")
        title.setProperty("class", "CardTitle")
        layout.addWidget(title)
        
        btn_add = QPushButton("+  Add more folders to sync")
        btn_add.setProperty("class", "PillActionButton")
        btn_add.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_add.clicked.connect(self._add_folder_to_sync)
        layout.addWidget(btn_add)
        
        btn_web = QPushButton("↗  Open Drive web")
        btn_web.setProperty("class", "PillActionButton")
        btn_web.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_web.clicked.connect(self._open_drive_web)
        layout.addWidget(btn_web)
        
        btn_offline = QPushButton("↗  Learn more about offline files")
        btn_offline.setProperty("class", "PillActionButton")
        btn_offline.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_offline.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://support.google.com/drive/answer/2375012")))
        layout.addWidget(btn_offline)
        
        btn_faq = QPushButton("↗  Frequently asked questions")
        btn_faq.setProperty("class", "PillActionButton")
        btn_faq.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_faq.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://support.google.com/drive")))
        layout.addWidget(btn_faq)
        
        layout.addStretch()
        return card

    # Acciones 100% cableadas
    def _open_drive_folder(self):
        target = self.backend.root_drive_path
        if not os.path.exists(target):
            self.backend.setup_file_explorer_integration()
        subprocess.Popen(["xdg-open", target])
        self.hide()

    def _open_shared_drive(self):
        target = os.path.join(self.backend.root_drive_path, "Compartido conmigo")
        if os.path.exists(target):
            subprocess.Popen(["xdg-open", target])
        else:
            QDesktopServices.openUrl(QUrl("https://drive.google.com/drive/shared-with-me"))
        self.hide()

    def _show_account_dialog(self):
        from account_dialog import GoogleAccountDialog
        dialog = GoogleAccountDialog(self.backend, self)
        dialog.open_preferences_requested.connect(self._open_preferences)
        dialog.login_requested.connect(self.open_preferences_requested.emit)
        dialog.exec()

    def _open_drive_web(self):
        QDesktopServices.openUrl(QUrl("https://drive.google.com"))
        self.hide()

    def _open_preferences(self):
        self.hide()
        self.open_preferences_requested.emit()

    def _on_search(self):
        query = self.search_input.text().strip()
        if query:
            url = f"https://drive.google.com/drive/search?q={query}"
            QDesktopServices.openUrl(QUrl(url))
            self.search_input.clear()
            self.hide()

    def _toggle_pause_sync(self):
        if self.backend.is_mounted():
            self.backend.cierre_seguro()
            self.pause_btn.setIcon(QIcon(get_asset("ic_sync_grey_24px.svg")))
            self.pause_btn.setToolTip("Reanudar sincronización")
        else:
            self.backend.start_mount()
            self.pause_btn.setIcon(QIcon(get_asset("ic_pause_circle_outline_grey600_24px.svg")))
            self.pause_btn.setToolTip("Pausar sincronización")
        self.sync_toggled.emit()

    def _add_folder_to_sync(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta local para sincronizar con Drive")
        if folder:
            dest_name = os.path.basename(folder)
            self.backend.start_bisync(folder, dest_name)
        self.hide()

    def toggle_popup(self, tray_geometry=None):
        if self.isVisible():
            self.hide()
        else:
            if tray_geometry and not tray_geometry.isNull():
                x = tray_geometry.x() - (self.width() // 2)
                y = tray_geometry.y() - self.height() - 10
                x = max(10, min(x, 1920 - self.width() - 10))
                y = max(10, y)
                self.move(x, y)
            else:
                cursor_pos = QCursor.pos()
                self.move(max(10, cursor_pos.x() - (self.width() // 2)), max(10, cursor_pos.y() - self.height() - 10))
            self.show()
            self.raise_()
            self.activateWindow()
