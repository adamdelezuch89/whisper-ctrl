#!/bin/bash

# Stops the script if any command returns an error
set -e

# --- Configuration ---
APP_NAME="Whisper-Ctrl"
MAIN_SCRIPT="main.py"
ICON_FILE="icon.png"
REQS_FILE="requirements.txt"
BUILD_TOOLS_DIR=".build_tools"

# --- Messages and colors ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Function to download tools ---
ensure_tool() {
    local tool_path=$1
    local tool_url=$2
    if [ ! -f "$tool_path" ]; then
        echo -e "${YELLOW}Tool '$(basename "$tool_path")' not found. Downloading...${NC}"
        wget --show-progress -O "$tool_path" "$tool_url"
        echo -e "${GREEN}Downloaded successfully.${NC}"
    fi
    chmod +x "$tool_path"
}

echo -e "${GREEN}--- Starting the AppImage build process for $APP_NAME ---${NC}"

# --- Step 1: Prepare Python environment ---
echo -e "${YELLOW}Step 1: Preparing Python environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating new virtual environment 'venv'..."
    python3 -m venv venv
else
    echo "Found existing 'venv' environment."
fi

source venv/bin/activate
echo "Installing/updating dependencies from $REQS_FILE..."
pip install -r "$REQS_FILE"

# --- Step 2: Prepare build tools ---
echo -e "${YELLOW}Step 2: Preparing build tools...${NC}"
mkdir -p "$BUILD_TOOLS_DIR"
LINUXDEPLOY_EXEC="$BUILD_TOOLS_DIR/linuxdeploy-x86_64.AppImage"
APPIMAGETOOL_EXEC="$BUILD_TOOLS_DIR/appimagetool-x86_64.AppImage"

ensure_tool "$LINUXDEPLOY_EXEC" "https://github.com/linuxdeploy/linuxdeploy/releases/latest/download/linuxdeploy-x86_64.AppImage"
ensure_tool "$APPIMAGETOOL_EXEC" "https://github.com/AppImage/AppImageKit/releases/latest/download/appimagetool-x86_64.AppImage"
echo -e "${GREEN}Build tools are ready and have execute permissions.${NC}"

# --- Step 3: Clean up old artifacts ---
echo -e "${YELLOW}Step 3: Cleaning up previous builds...${NC}"
rm -rf AppDir "${APP_NAME}"-*.AppImage*

# --- Step 4: Build the AppDir structure ---
echo -e "${YELLOW}Step 4: Packaging the interpreter and libraries...${NC}"

# FIX: Explicitly create directories to prevent "No such file or directory" error.
# This makes the script more reliable in case linuxdeploy doesn't create them itself.
mkdir -p AppDir/usr/bin AppDir/usr/lib

"$LINUXDEPLOY_EXEC" --appdir AppDir --executable venv/bin/python3
cp "$MAIN_SCRIPT" AppDir/usr/bin/

PYTHON_VERSION_DIR=$(basename $(ls -d venv/lib/python*))
cp -r "venv/lib/$PYTHON_VERSION_DIR/site-packages" AppDir/usr/lib/
echo "Copied libraries from: venv/lib/$PYTHON_VERSION_DIR/site-packages"

# --- Step 5: Create metadata ---
echo -e "${YELLOW}Step 5: Creating the startup script and metadata...${NC}"
cat <<'EOF' > AppDir/AppRun
#!/bin/bash
APPDIR=$(dirname "$0")
export PYTHONPATH="$APPDIR/usr/lib/site-packages"
exec "$APPDIR/usr/bin/python3" "$APPDIR/usr/bin/main.py"
EOF
chmod +x AppDir/AppRun

cat <<EOF > AppDir/"${APP_NAME,,}".desktop
[Desktop Entry]
Name=$APP_NAME
Exec=AppRun
Icon=${APP_NAME,,}
Type=Application
Categories=Utility;AudioVideo;
Comment=Local speech-to-text transcription
EOF
cp "$ICON_FILE" AppDir/"${APP_NAME,,}".png

# --- Step 6: Build the final file ---
echo -e "${YELLOW}Step 6: Building the final AppImage file...${NC}"
"$APPIMAGETOOL_EXEC" AppDir

# --- Step 7: Final cleanup ---
echo -e "${YELLOW}Step 7: Removing all temporary files...${NC}"
rm -rf AppDir
rm -rf "$BUILD_TOOLS_DIR"

FINAL_APPIMAGE=$(ls -t "${APP_NAME}"-*.AppImage | head -n 1)
echo -e "${GREEN}--- SUCCESS! ---${NC}"
echo -e "Created file: ${GREEN}$FINAL_APPIMAGE${NC}"
echo -e "The 'venv' environment has been kept for further development work."