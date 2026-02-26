#!/bin/bash
# build.sh — Génère un .AppImage standalone pour pkgmanager
# Usage: chmod +x build.sh && ./build.sh
# Prérequis: Python 3.10+, pip, venv

set -e  # Arrêt immédiat si une commande échoue

APP_NAME="pkgmanager"
APP_VERSION="1.0.0"
ARCH="x86_64"
BUILD_DIR="dist/${APP_NAME}"
APPDIR="${APP_NAME}.AppDir"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Build ${APP_NAME} v${APP_VERSION}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Dépendances système ────────────────────────────────────────────────────
echo "[1/5] Vérification des dépendances..."
sudo apt-get install -y upx-ucl wget fuse libfuse2 2>/dev/null || true

# ── 2. Environnement virtuel + PyInstaller ────────────────────────────────────
echo "[2/5] Installation de PyInstaller..."
pip install pyinstaller --break-system-packages -q

# ── 3. Build PyInstaller ──────────────────────────────────────────────────────
echo "[3/5] Compilation avec PyInstaller..."
pyinstaller pkgmanager.spec --clean --noconfirm

echo "    ✓ Binaire généré dans dist/${APP_NAME}/"

# ── 4. Préparer le répertoire AppDir ─────────────────────────────────────────
echo "[4/5] Préparation AppDir..."

rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

# Copier le build PyInstaller dans AppDir
cp -r "${BUILD_DIR}/." "${APPDIR}/usr/bin/"

# Icône (adapte le chemin si besoin)
if [ -f "assets/icon.png" ]; then
    cp assets/icon.png "${APPDIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
    cp assets/icon.png "${APPDIR}/${APP_NAME}.png"
else
    # Créer une icône placeholder si absente
    echo "    ⚠ Pas d'icône trouvée dans assets/icon.png, icône par défaut utilisée"
    convert -size 256x256 xc:#4F9EFF -fill white -gravity Center \
        -font DejaVu-Sans -pointsize 80 -annotate 0 "PM" \
        "${APPDIR}/${APP_NAME}.png" 2>/dev/null || touch "${APPDIR}/${APP_NAME}.png"
fi

# Fichier .desktop
cat > "${APPDIR}/usr/share/applications/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Name=Package Manager
Comment=Manage manually installed APT and Snap packages
Exec=pkgmanager
Icon=${APP_NAME}
Type=Application
Categories=System;PackageManager;
Terminal=false
EOF

# Copie du .desktop à la racine AppDir (requis par AppImage)
cp "${APPDIR}/usr/share/applications/${APP_NAME}.desktop" "${APPDIR}/${APP_NAME}.desktop"

# Script AppRun — point d'entrée de l'AppImage
cat > "${APPDIR}/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export QT_QPA_PLATFORM_PLUGIN_PATH="${HERE}/usr/bin/PyQt6/Qt6/plugins/platforms"
export QT_PLUGIN_PATH="${HERE}/usr/bin/PyQt6/Qt6/plugins"
exec "${HERE}/usr/bin/pkgmanager" "$@"
EOF
chmod +x "${APPDIR}/AppRun"

# ── 5. Télécharger appimagetool et créer l'AppImage ──────────────────────────
echo "[5/5] Création de l'AppImage..."

if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "    Téléchargement de appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

ARCH=x86_64 ./appimagetool-x86_64.AppImage "${APPDIR}" "${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✓ AppImage créée : ${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"
echo " Lance avec : ./${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
