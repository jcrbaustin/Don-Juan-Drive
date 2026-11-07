"""
styles.py: Material 3 Design Tokens y QSS para Google Drive Linux.
Inspirado directamente en la interfaz oficial de Google Workspace / Google Drive Desktop.
"""

MATERIAL_STYLE = """
/* Global */
QWidget {
    font-family: "Google Sans", "Roboto", "Segoe UI", "Ubuntu", "Cantarell", sans-serif;
    color: #1F1F1F;
    background-color: transparent;
    font-size: 13px;
}

/* Ventana emergente (Popup Tray) */
#DrivePopup {
    background-color: #F0F4F9;
    border: 1px solid #C4C7C5;
    border-radius: 18px;
}

/* Barra superior / Header */
#HeaderContainer {
    background-color: #F0F4F9;
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
    padding: 10px 16px;
}

#AppTitle {
    font-size: 18px;
    font-weight: 600;
    color: #1F1F1F;
}

/* Buscador en píldora */
#SearchBar {
    background-color: #E9EEF6;
    border: none;
    border-radius: 18px;
    padding: 6px 14px 6px 36px;
    font-size: 13px;
    color: #1F1F1F;
}
#SearchBar:focus {
    background-color: #FFFFFF;
    border: 1px solid #0B57D0;
}

/* Botones de acción del header */
QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 18px;
    padding: 6px;
}
QToolButton:hover {
    background-color: #E1E3E1;
}
QToolButton:pressed {
    background-color: #D3E3FD;
}

/* Avatar del usuario */
#AvatarButton {
    background-color: #0B57D0;
    color: #FFFFFF;
    font-weight: bold;
    border-radius: 16px;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    text-align: center;
}

/* Barra lateral / Drawer */
#DrawerContainer {
    background-color: #F0F4F9;
    padding: 8px 12px;
    min-width: 170px;
    max-width: 170px;
}

/* Botón grande: Abrir carpeta de Drive */
#OpenDriveFolderBtn {
    background-color: #FFFFFF;
    border: 1px solid #747775;
    border-radius: 16px;
    padding: 8px 12px;
    font-weight: 500;
    text-align: left;
}
#OpenDriveFolderBtn:hover {
    background-color: #F8FAFD;
    border-color: #0B57D0;
}

/* Pestañas de la barra lateral */
.DrawerTab {
    background-color: transparent;
    border: none;
    border-radius: 18px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
    color: #444746;
}
.DrawerTab:hover {
    background-color: #E9EEF6;
    color: #1F1F1F;
}
.DrawerTab[selected="true"] {
    background-color: #D3E3FD;
    color: #041E49;
    font-weight: 600;
}

/* Tarjetas Bento del contenido principal */
.BentoCard {
    background-color: #FFFFFF;
    border: 1px solid #E0E2EC;
    border-radius: 16px;
    padding: 16px;
}
.BentoCard:hover {
    border-color: #C4C7C5;
}

.CardTitle {
    font-size: 15px;
    font-weight: 600;
    color: #1F1F1F;
}

.CardSubtitle {
    font-size: 12px;
    color: #444746;
    line-height: 1.4;
}

/* Botones de acción dentro de las tarjetas */
.PillActionButton {
    background-color: #FFFFFF;
    border: 1px solid #747775;
    border-radius: 14px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    color: #1F1F1F;
}
.PillActionButton:hover {
    background-color: #F8FAFD;
    border-color: #0B57D0;
    color: #0B57D0;
}

/* Botón primario azul */
.PrimaryButton {
    background-color: #0B57D0;
    color: #FFFFFF;
    border: none;
    border-radius: 18px;
    padding: 8px 22px;
    font-weight: 600;
    font-size: 13px;
}
.PrimaryButton:hover {
    background-color: #0842A0;
}
.PrimaryButton:pressed {
    background-color: #041E49;
}

/* Botón secundario/cancelar */
.SecondaryButton {
    background-color: transparent;
    color: #0B57D0;
    border: 1px solid #747775;
    border-radius: 18px;
    padding: 8px 20px;
    font-weight: 500;
    font-size: 13px;
}
.SecondaryButton:hover {
    background-color: #E9EEF6;
}

/* Ventana de Preferencias */
#PreferencesWindow {
    background-color: #FFFFFF;
}

#PreferencesSidebar {
    background-color: #F8FAFD;
    border-right: 1px solid #E0E2EC;
    padding: 16px 8px;
}

.PrefSectionTitle {
    font-size: 17px;
    font-weight: 600;
    color: #1F1F1F;
}

.PrefSubtitle {
    font-size: 13px;
    color: #444746;
}

/* Radio buttons estilizados */
QRadioButton {
    font-size: 14px;
    font-weight: 600;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #747775;
    background-color: #FFFFFF;
}
QRadioButton::indicator:checked {
    border-color: #0B57D0;
    background-color: #0B57D0;
}

/* Cuadro de llamada azul de información */
#InfoBanner {
    background-color: #E8F0FE;
    border: 1px solid #D3E3FD;
    border-radius: 12px;
    padding: 12px 14px;
    color: #041E49;
    font-size: 12px;
}

/* Lista de Actividad Reciente */
.ActivityCard {
    background-color: #FFFFFF;
    border-radius: 12px;
    padding: 10px 14px;
    border: 1px solid #E0E2EC;
}
.ActivityCard:hover {
    background-color: #F8FAFD;
    border-color: #C4C7C5;
}
.ActivityFileName {
    font-size: 13px;
    font-weight: 500;
    color: #1F1F1F;
}
.ActivityMeta {
    font-size: 11px;
    color: #747775;
}

/* ScrollArea limpio */
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #C4C7C5;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #747775;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

