#!/bin/bash
# build_snap.sh — Compile et publie le snap LinuxPkgManager
# Usage: chmod +x build_snap.sh && ./build_snap.sh

set -e

APP_NAME="linuxpkgmanager"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Build Snap — ${APP_NAME}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Installer snapcraft ────────────────────────────────────────────────────
echo "[1/4] Installation de snapcraft..."
sudo snap install snapcraft --classic 2>/dev/null || echo "    snapcraft déjà installé"

# ── 2. Préparer le .desktop ───────────────────────────────────────────────────
echo "[2/4] Préparation des fichiers..."
mkdir -p usr/share/applications
cp snap/linuxpkgmanager.desktop usr/share/applications/

# ── 3. Build du snap ──────────────────────────────────────────────────────────
echo "[3/4] Compilation du snap (peut prendre quelques minutes)..."
snapcraft --destructive-mode
# Note: --destructive-mode build directement sur ta machine sans LXD/Multipass
# Si tu veux un environnement isolé, retire --destructive-mode (nécessite LXD)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✓ Snap créé : ${APP_NAME}_1.0.0_amd64.snap"
echo ""
echo " Tester localement :"
echo "   sudo snap install ${APP_NAME}_1.0.0_amd64.snap --classic --dangerous"
echo ""
echo " Publier sur le Snap Store :"
echo "   snapcraft login"
echo "   snapcraft upload ${APP_NAME}_1.0.0_amd64.snap --release=stable"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
