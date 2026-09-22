#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/1024x1024/apps"
mkdir -p "$APP_DIR" "$ICON_DIR"
cp "$ROOT/assets/icon-mk.png" "$ICON_DIR/apison.png"
sed -e "s|^Exec=.*|Exec=$ROOT/start_gui.sh|" -e 's|^Icon=.*|Icon=apison|' \
  "$ROOT/APIson.desktop" > "$APP_DIR/apison.desktop"
chmod +x "$APP_DIR/apison.desktop"
echo "APIson 已加入应用菜单。"
