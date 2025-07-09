#!/bin/bash

# Stops the script if any command returns an error.
# This is crucial for reliable build scripts.
set -e

# --- Configuration ---
# All configuration variables are in one place for easy access.
# Use lowercase for the package name, as per Debian policy.
APP_NAME="whisper-ctrl"
VERSION="1.0-1" # Remember to increment this value for each new build.

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
cp main.py "$BUILD_DIR/usr/lib/$APP_NAME/"
cp icon.png "$BUILD_DIR/usr/share/pixmaps/$APP_NAME.png"

# --- Step 5: Create metadata and scripts ---
echo -e "${YELLOW}Step 5: Creating DEBIAN files, .desktop entry, and launcher script...${NC}"

# 5a: The 'control' file - the heart of the package.
# IMPORTANT: Change the 'Maintainer' field to your name and email.
cat <<EOF > "$BUILD_DIR/DEBIAN/control"
Package: ${APP_NAME}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: Your Name <your.email@example.com>
Depends: python3, xclip, xdotool, wl-clipboard, wtype, libnotify-bin, sounddevice
Description: Local GPU-accelerated speech-to-text dictation.
 Whisper-Ctrl is a lightweight voice dictation application for Linux that
 leverages the power of your local GPU for fast speech-to-text transcription.
 .
 IMPORTANT: This application requires an NVIDIA graphics card with correctly
 installed drivers and CUDA Toolkit (11 or 12). It will not work without them.
 .
 This package bundles heavy dependencies like PyTorch and faster-whisper
 to ensure it works out-of-the-box on a configured system.
EOF

# 5b: The 'postinst' script - runs after installation to inform the user.
cat <<'EOF' > "$BUILD_DIR/DEBIAN/postinst"
#!/bin/bash
set -e
echo "--------------------------------------------------------"
echo "Whisper-Ctrl has been installed."
echo ""
echo "IMPORTANT REQUIREMENTS:"
echo "1. This application REQUIRES an NVIDIA GPU with CUDA drivers."
echo "2. For global hotkeys to work, add your user to the 'input' group:"
echo ""
echo "     sudo usermod -a -G input \$USER"
echo ""
echo "You must log out and log back in for this change to take effect."
echo "--------------------------------------------------------"
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
find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -r {} +
find "$BUILD_DIR" -type f -name "*.pyc" -delete

# --- Step 7: Build the .deb package using fakeroot ---
echo -e "${YELLOW}Step 7: Building the final .deb package...${NC}"
# We use fakeroot to simulate root permissions for files inside the package,
# without needing to run the entire script as root.
fakeroot dpkg-deb --build "$BUILD_DIR"

# --- Step 8: Clean up ---
echo -e "${YELLOW}Step 8: Cleaning up the temporary build directory...${NC}"
rm -r "$BUILD_DIR"

FINAL_DEB="${APP_NAME}_${VERSION}_${ARCH}.deb"
echo -e "${GREEN}--- SUCCESS! ---${NC}"
echo -e "Created package: ${GREEN}$FINAL_DEB${NC}"
echo -e "You can now install it using: ${YELLOW}sudo apt install ./$FINAL_DEB${NC}"