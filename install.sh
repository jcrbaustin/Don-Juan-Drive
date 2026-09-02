#!/bin/bash
set -e

APP_NAME="DonJuanDrive"
EXEC_NAME="don-juan-drive"
DESKTOP_FILE="$APP_NAME.desktop"

echo "=== Instalando Don Juan Drive for Linux ==="

# 1. Crear entorno y compilar
echo "[1/4] Preparando entorno virtual y compilando con PyInstaller..."
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller

# Compilar un solo ejecutable sin consola e inyectar los iconos (assets)
pyinstaller --noconsole --onefile --add-data "icon_gray.png:." --add-data "icon_color.png:." --add-data "drive_color.png:." --add-data "drive_gris.png:." --name="$EXEC_NAME" main.py
deactivate

# 2. Copiar ejecutable a ~/.local/bin
echo "[2/4] Instalando ejecutable en ~/.local/bin..."
mkdir -p ~/.local/bin
cp "dist/$EXEC_NAME" ~/.local/bin/
chmod +x ~/.local/bin/"$EXEC_NAME"

# 3. Crear el archivo .desktop
echo "[3/4] Generando archivo de escritorio (.desktop)..."
cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Name=Don Juan Drive For Linux
Comment=Cliente nativo de Google Drive para Linux (rclone vfs)
Exec=$HOME/.local/bin/$EXEC_NAME
Icon=drive-cloud
Terminal=false
Type=Application
Categories=Network;FileTransfer;
StartupNotify=false
EOF

# 4. Mover a Applications
echo "[4/4] Añadiendo al menú de aplicaciones..."
mkdir -p ~/.local/share/applications
cp "$DESKTOP_FILE" ~/.local/share/applications/

echo "=== Instalación Completada ==="
echo "La aplicación se iniciará sola al encender tu computadora."
echo "Puedes ejecutar '$EXEC_NAME' desde la terminal o buscar 'Don Juan Drive' en tu menú principal."
