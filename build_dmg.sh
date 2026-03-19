#!/bin/bash
# ──────────────────────────────────────────────────────────────
# build_dmg.sh — Build my.File Tool into a macOS .dmg
# ──────────────────────────────────────────────────────────────
# Creates a drag-and-drop DMG installer with:
#   - The .app bundle (via py2app)
#   - An Applications folder shortcut
#   - A styled background image
#
# Usage:
#   chmod +x build_dmg.sh
#   ./build_dmg.sh
#
# Prerequisites:
#   pip3 install PyQt5 py2app
# ──────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="my.File Tool"
DMG_NAME="MyFileTool"
DMG_VOLUME_NAME="my.File Tool"
ICON_SET="MyhFileFinder.iconset"
ICON_ICNS="MyhFileFinder.icns"
BG_IMAGE="dmg_background.png"

# Read version from VERSION file
VERSION_FILE="${SCRIPT_DIR}/VERSION"
if [ ! -f "$VERSION_FILE" ]; then
    echo "  ERROR: VERSION file not found at $VERSION_FILE"
    exit 1
fi
APP_VERSION=$(tr -d '[:space:]' < "$VERSION_FILE")

DMG_FINAL="${DMG_NAME}-${APP_VERSION}.dmg"
DMG_TEMP="${DMG_NAME}_temp.dmg"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  my.File Tool v${APP_VERSION} — DMG Builder"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Step 1: Check dependencies ────────────────────────────
echo ""
echo "▶ [1/6] Checking dependencies..."

if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo "  Installing PyQt5..."
    pip3 install PyQt5
else
    echo "  ✓ PyQt5"
fi

if ! python3 -c "import py2app" 2>/dev/null; then
    echo "  Installing py2app..."
    pip3 install py2app
else
    echo "  ✓ py2app"
fi

# ── Step 2: Generate .icns icon ───────────────────────────
echo ""
echo "▶ [2/6] Generating app icon..."

if [ -d "$ICON_SET" ]; then
    iconutil -c icns "$ICON_SET" -o "$ICON_ICNS" 2>/dev/null && \
        echo "  ✓ $ICON_ICNS created from iconset" || \
        echo "  ⚠ iconutil failed — will use fallback"
elif [ -f "app_icon.png" ]; then
    echo "  Creating iconset from app_icon.png..."
    mkdir -p "$ICON_SET"
    for SIZE in 16 32 64 128 256 512; do
        sips -z $SIZE $SIZE app_icon.png --out "${ICON_SET}/icon_${SIZE}x${SIZE}.png" >/dev/null 2>&1
    done
    for SIZE in 16 32 64 128 256; do
        DOUBLE=$((SIZE * 2))
        sips -z $DOUBLE $DOUBLE app_icon.png --out "${ICON_SET}/icon_${SIZE}x${SIZE}@2x.png" >/dev/null 2>&1
    done
    iconutil -c icns "$ICON_SET" -o "$ICON_ICNS" 2>/dev/null && \
        echo "  ✓ $ICON_ICNS created" || \
        echo "  ⚠ iconutil failed"
elif [ -f "$ICON_ICNS" ]; then
    echo "  ✓ $ICON_ICNS already exists"
else
    echo "  ⚠ No icon source found — using default Python icon"
fi

# ── Step 3: Build .app with py2app ────────────────────────
echo ""
echo "▶ [3/6] Building .app bundle..."

rm -rf build dist

python3 setup.py py2app 2>&1 | while IFS= read -r line; do
    case "$line" in
        *error*|*Error*|*WARNING*) echo "  $line" ;;
        *copying*PyQt5*) ;;
        *"creating"*".app"*) echo "  $line" ;;
    esac
done

APP_PATH="dist/${APP_NAME}.app"
if [ ! -d "$APP_PATH" ]; then
    echo "  ✗ py2app build failed. Try running manually:"
    echo "    python3 setup.py py2app"
    exit 1
fi
echo "  ✓ ${APP_NAME}.app built"

# ── Step 3b: Code sign ───────────────────────────────────
# Set CODESIGN_IDENTITY to sign the app. Options:
#   - Harvard enterprise cert: "Developer ID Application: President and Fellows of Harvard College (XXXXXXXXXX)"
#   - Self-signed (local dev): "myh-file-finder"  (create in Keychain Access first)
#   - Ad-hoc (no cert needed):  "-"
#   - Skip signing:             leave empty
CODESIGN_IDENTITY="${CODESIGN_IDENTITY:-}"

if [ -n "$CODESIGN_IDENTITY" ]; then
    echo ""
    echo "▶ [3b] Code signing with: ${CODESIGN_IDENTITY}..."
    codesign --force --deep -s "$CODESIGN_IDENTITY" "$APP_PATH" 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✓ Signed"
    else
        echo "  ⚠ Signing failed — continuing without signature"
    fi
else
    echo ""
    echo "  ⚠ No CODESIGN_IDENTITY set — app will be unsigned"
    echo "    To sign: export CODESIGN_IDENTITY='Your Certificate Name'"
fi

# ── Step 4: Create DMG staging area ──────────────────────
echo ""
echo "▶ [4/6] Staging DMG contents..."

# Generate drag-to-Applications background if missing
if [ ! -f "$BG_IMAGE" ]; then
    echo "  Generating drag-to-Applications background..."
    python3 make_dmg_background.py 2>/dev/null || true
fi

STAGING="dist/dmg_staging"
rm -rf "$STAGING"
mkdir -p "$STAGING/.background"

# Copy the .app
cp -R "$APP_PATH" "$STAGING/"

# Create Applications symlink
ln -s /Applications "$STAGING/Applications"

# Copy background image (required for drag-to-Applications UI)
if [ -f "$BG_IMAGE" ]; then
    cp "$BG_IMAGE" "$STAGING/.background/background.png"
    echo "  ✓ Background image added (drag to Applications layout)"
else
    echo "  ⚠ No background image — run: python3 make_dmg_background.py"
fi

echo "  ✓ Staging complete"

# ── Step 5: Create the DMG ───────────────────────────────
echo ""
echo "▶ [5/6] Creating DMG..."

rm -f "$DMG_FINAL" "$DMG_TEMP"

# Create a read/write DMG first so we can style it
hdiutil create \
    -srcfolder "$STAGING" \
    -volname "$DMG_VOLUME_NAME" \
    -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" \
    -format UDRW \
    -size 400m \
    "$DMG_TEMP" \
    >/dev/null 2>&1

echo "  ✓ Temp DMG created"

# ── Step 6: Style the DMG Finder window ──────────────────
echo ""
echo "▶ [6/6] Styling DMG window..."

# Eject any stale mounts of the same volume name
hdiutil detach "/Volumes/$DMG_VOLUME_NAME" 2>/dev/null || true
for i in $(seq 1 20); do
    hdiutil detach "/Volumes/${DMG_VOLUME_NAME} ${i}" 2>/dev/null || true
done
sleep 1

# Mount the temp DMG
MOUNT_DIR=$(hdiutil attach -readwrite -noverify "$DMG_TEMP" | grep "/Volumes/" | sed 's/.*\/Volumes/\/Volumes/')
echo "  Mounted at: $MOUNT_DIR"

# Extract the actual volume name Finder sees (may include a number suffix)
ACTUAL_VOL_NAME=$(basename "$MOUNT_DIR")
echo "  Volume name: $ACTUAL_VOL_NAME"

sleep 2

# Hide dotfiles BEFORE styling so they don't appear
chflags hidden "$MOUNT_DIR/.background" 2>/dev/null || true
chflags hidden "$MOUNT_DIR/.fseventsd" 2>/dev/null || true
chflags hidden "$MOUNT_DIR/.Trashes" 2>/dev/null || true

# Use AppleScript to configure the Finder window
# IMPORTANT: Use the ACTUAL volume name (may have suffix like "my.File Tool 2")
osascript <<APPLESCRIPT
tell application "Finder"
    tell disk "$ACTUAL_VOL_NAME"
        open
        delay 2
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set bounds of container window to {200, 200, 860, 640}

        set theViewOptions to icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to 100
        set text size of theViewOptions to 13

        -- Set background using HFS colon-path (reliable on all macOS versions)
        set background picture of theViewOptions to file ".background:background.png"

        -- Position: app on left, Applications on right (centered in 660x440 window)
        set position of item "${APP_NAME}.app" to {165, 220}
        set position of item "Applications" to {495, 220}

        update without registering applications
        delay 2
    end tell
end tell
APPLESCRIPT

# Keep window open so Finder commits .DS_Store
sleep 4
osascript -e "tell application \"Finder\" to close (every window whose name is \"$ACTUAL_VOL_NAME\")" 2>/dev/null || true
sleep 2

# Unmount
hdiutil detach "$MOUNT_DIR" >/dev/null 2>&1
echo "  ✓ Styled"

# Convert to compressed, read-only final DMG
hdiutil convert "$DMG_TEMP" \
    -format UDZO \
    -imagekey zlib-level=9 \
    -o "$DMG_FINAL" \
    >/dev/null 2>&1

rm -f "$DMG_TEMP"

# Also create a version-less copy for stable download links
DMG_LATEST="${DMG_NAME}-latest.dmg"
cp "$DMG_FINAL" "$DMG_LATEST"

# ── Done ─────────────────────────────────────────────────
echo ""
DMG_SIZE=$(du -sh "$DMG_FINAL" | cut -f1)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ DMG created successfully!"
echo ""
echo "  File: $DMG_FINAL"
echo "  Size: $DMG_SIZE"
echo ""
echo "  To install:"
echo "    1. Double-click $DMG_FINAL"
echo "    2. Drag 'my.File Tool' → Applications"
echo "    3. Eject the disk image"
echo "    4. Launch from Applications / Spotlight"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
