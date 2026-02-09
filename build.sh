#!/bin/bash

# Stops the script if any command returns an error.
# This is crucial for reliable build scripts.
set -e

# --- Configuration ---
# All configuration variables are in one place for easy access.
# Use lowercase for the package name, as per Debian policy.
APP_NAME="whisper-ctrl"
VERSION="2.0-1" # v2.0: Modular architecture, multi-backend, cross-platform

# The architecture is dynamically fetched from the build system.
# This makes the script portable (e.g., to ARM machines).
ARCH=$(dpkg --print-architecture)

# The build directory name is dynamically created from the variables above.
BUILD_DIR="${APP_NAME}_${VERSION}_${ARCH}"
# The directory where we will place all Python dependencies.
LIB_DIR="$BUILD_DIR/usr/lib/$APP_NAME/lib"

# --- Colors and messages ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}--- Starting the .deb package build process for $APP_NAME ---${NC}"

# --- Step 1: Clean up previous builds ---
echo -e "${YELLOW}Step 1: Cleaning up previous artifacts...${NC}"
rm -rf "$BUILD_DIR" "${APP_NAME}"_*.deb

# --- Step 2: Create directory structure compliant with FHS ---
echo -e "${YELLOW}Step 2: Creating the package directory structure...${NC}"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$LIB_DIR" # This also creates /usr/lib/$APP_NAME
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/pixmaps"

# --- Step 3: Install Python dependencies directly into the target directory ---
echo -e "${YELLOW}Step 3: Installing Python dependencies...${NC}"
echo "This may take a while due to the size of the libraries."
# Using '--target' is cleaner and more efficient than creating a venv and copying.
pip install --target="$LIB_DIR" -r requirements.txt

# --- Step 4: Copy application files ---
echo -e "${YELLOW}Step 4: Copying application files...${NC}"
# Copy main entry point
cp main.py "$BUILD_DIR/usr/lib/$APP_NAME/"

# Copy modular structure (v2.0)
cp -r core "$BUILD_DIR/usr/lib/$APP_NAME/"
cp -r transcribers "$BUILD_DIR/usr/lib/$APP_NAME/"
cp -r ui "$BUILD_DIR/usr/lib/$APP_NAME/"

# Copy icon
cp icon.png "$BUILD_DIR/usr/share/pixmaps/$APP_NAME.png"

echo "Copied modular structure: core/, transcribers/, ui/"

# --- Step 5: Create metadata and scripts ---
echo -e "${YELLOW}Step 5: Creating DEBIAN files, .desktop entry, and launcher script...${NC}"

# 5a: The 'control' file - the heart of the package.
# IMPORTANT: Change the 'Maintainer' field to your name and email.
cat <<EOF > "$BUILD_DIR/DEBIAN/control"
Package: ${APP_NAME}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: Your Name <your.email@example.com>
Depends: python3, xclip, xdotool, wl-clipboard, wtype, libnotify-bin
Description: Multi-backend voice dictation (Local GPU or OpenAI API)
 Whisper-Ctrl v2.0 is a cross-platform voice dictation application with
 flexible transcription backends: local GPU (faster-whisper) or cloud API (OpenAI).
 .
 Features:
  - Multi-backend: Switch between Local GPU and OpenAI API
  - Cross-platform: Supports Linux (X11/Wayland) and Windows
  - Settings GUI: Easy configuration with PySide6
  - System tray integration with quick access menu
  - Voice Activity Detection (VAD) for better accuracy
 .
 For Local GPU backend: Requires NVIDIA GPU with CUDA 11/12 drivers.
 For OpenAI API backend: Requires API key (no GPU needed).
 .
 This package bundles all Python dependencies including PyTorch, faster-whisper,
 and PySide6 to ensure out-of-the-box functionality.
EOF

# 5b: The 'postinst' script - runs after installation to inform the user.
cat <<'EOF' > "$BUILD_DIR/DEBIAN/postinst"
#!/bin/bash
set -e
echo "=========================================================="
echo "Whisper-Ctrl v2.0 has been installed successfully!"
echo "=========================================================="
echo ""
echo "QUICK START:"
echo "1. Run: whisper-ctrl"
echo "2. Configure backend (Local GPU or OpenAI API) in Settings"
echo "3. Use: Double-press Ctrl to start/stop recording"
echo ""
echo "REQUIREMENTS:"
echo ""
echo "For Local GPU backend:"
echo "  • NVIDIA GPU with CUDA 11 or 12 drivers"
echo "  • ~2-10GB VRAM (depending on model size)"
echo ""
echo "For OpenAI API backend:"
echo "  • OpenAI API key (get from platform.openai.com)"
echo "  • Internet connection"
echo "  • No GPU required"
echo ""
echo "PERMISSIONS:"
echo "For global hotkeys to work, add your user to 'input' group:"
echo ""
echo "  sudo usermod -a -G input \$USER"
echo ""
echo "Then log out and back in for changes to take effect."
echo ""
echo "=========================================================="

# Ask about autostart
echo ""
read -p "Do you want to add Whisper-Ctrl to autostart? [y/N]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Get the real user (not root)
    if [ -n "$SUDO_USER" ]; then
        REAL_USER="$SUDO_USER"
        REAL_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    else
        REAL_USER="$USER"
        REAL_HOME="$HOME"
    fi

    # Create autostart directory if it doesn't exist
    AUTOSTART_DIR="$REAL_HOME/.config/autostart"
    sudo -u "$REAL_USER" mkdir -p "$AUTOSTART_DIR"

    # Create autostart .desktop file
    AUTOSTART_FILE="$AUTOSTART_DIR/whisper-ctrl.desktop"
    cat > "$AUTOSTART_FILE" <<AUTOSTART
[Desktop Entry]
Version=1.0
Name=Whisper-Ctrl
Comment=Local speech-to-text transcription via GPU
Exec=/usr/bin/whisper-ctrl
Icon=/usr/share/pixmaps/whisper-ctrl.png
Terminal=false
Type=Application
Categories=Utility;AudioVideo;
StartupNotify=false
X-GNOME-Autostart-enabled=true
AUTOSTART

    # Set correct ownership
    chown "$REAL_USER":"$REAL_USER" "$AUTOSTART_FILE"
    chmod 644 "$AUTOSTART_FILE"

    echo "✅ Whisper-Ctrl added to autostart"
else
    echo "⏭️  Skipped autostart setup"
fi

echo ""
echo "=========================================================="
echo "Launch app: whisper-ctrl"
echo "Settings: Right-click tray icon"
echo "Docs: /usr/share/doc/whisper-ctrl/"
echo "=========================================================="
exit 0
EOF

# 5c: The launcher script, which sets the PYTHONPATH.
cat <<EOF > "$BUILD_DIR/usr/bin/$APP_NAME"
#!/bin/bash
APP_LIB_PATH="/usr/lib/$APP_NAME/lib"
export PYTHONPATH="\${APP_LIB_PATH}:\${PYTHONPATH}"
exec python3 /usr/lib/$APP_NAME/main.py "\$@"
EOF

# 5d: The .desktop file - for application menu integration.
cat <<EOF > "$BUILD_DIR/usr/share/applications/$APP_NAME.desktop"
[Desktop Entry]
Version=1.0
Name=Whisper-Ctrl
Comment=Local speech-to-text transcription via GPU
Exec=/usr/bin/$APP_NAME
Icon=/usr/share/pixmaps/$APP_NAME.png
Terminal=false
Type=Application
Categories=Utility;AudioVideo;
StartupNotify=false
EOF

# --- Step 6: Set correct executable permissions ---
echo -e "${YELLOW}Step 6: Setting executable permissions...${NC}"
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/usr/bin/$APP_NAME"

# --- Step 6.5: Clean up bytecode files to reduce package size ---
echo -e "${YELLOW}Step 6.5: Cleaning up bytecode files...${NC}"
find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

# --- Step 6.6: Sync filesystem to prevent file-changed errors ---
echo -e "${YELLOW}Step 6.6: Syncing filesystem...${NC}"
sync
sleep 2

# --- Step 7: Build the .deb package using fakeroot ---
echo -e "${YELLOW}Step 7: Building the final .deb package...${NC}"
# We use fakeroot to simulate root permissions for files inside the package,
# without needing to run the entire script as root.
fakeroot dpkg-deb --build --root-owner-group "$BUILD_DIR"

# --- Step 8: Clean up ---
echo -e "${YELLOW}Step 8: Cleaning up the temporary build directory...${NC}"
rm -r "$BUILD_DIR"

FINAL_DEB="${APP_NAME}_${VERSION}_${ARCH}.deb"
echo -e "${GREEN}--- SUCCESS! ---${NC}"
echo -e "Created package: ${GREEN}$FINAL_DEB${NC}"
echo -e "You can now install it using: ${YELLOW}sudo apt install ./$FINAL_DEB${NC}"