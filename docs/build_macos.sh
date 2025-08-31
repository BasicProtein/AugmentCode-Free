#!/bin/bash
# macOS Build Script for AugmentCode-Free
# Fixes common macOS PyInstaller issues

set -e  # Exit on any error

VERSION="2.0.4"
APP_NAME="AugmentCode-Free"

echo "🍎 Building AugmentCode-Free v${VERSION} for macOS..."

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python version: ${python_version}"

if [[ $(echo "${python_version} < 3.7" | bc -l) -eq 1 ]]; then
    echo "❌ Python 3.7+ required, found ${python_version}"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 install pyinstaller

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.spec

# Create temporary directory with proper permissions
TEMP_DIR=$(mktemp -d)
echo "📁 Using temporary directory: ${TEMP_DIR}"

# Copy source files to temp directory
echo "📋 Copying source files..."
cp -r . "${TEMP_DIR}/"
cd "${TEMP_DIR}"

# Set proper permissions
chmod -R 755 .

# Build standalone executable (recommended for compatibility)
echo "🔨 Building standalone executable..."
pyinstaller --onefile \
    --name "${APP_NAME}-v${VERSION}-macos-standalone" \
    --add-data "languages:languages" \
    --add-data "config:config" \
    --add-data "augment_tools_core:augment_tools_core" \
    --add-data "gui_qt6:gui_qt6" \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=psutil \
    --hidden-import=sqlite3 \
    --hidden-import=xml.etree.ElementTree \
    --hidden-import=pathlib \
    --hidden-import=json \
    --hidden-import=uuid \
    --hidden-import=platform \
    --hidden-import=subprocess \
    --hidden-import=threading \
    --hidden-import=queue \
    --hidden-import=shutil \
    --hidden-import=tempfile \
    --collect-all=PyQt6 \
    --clean \
    main.py

# Build app bundle
echo "🔨 Building app bundle..."
pyinstaller --onefile --windowed \
    --name "${APP_NAME}-v${VERSION}-macos" \
    --add-data "languages:languages" \
    --add-data "config:config" \
    --add-data "augment_tools_core:augment_tools_core" \
    --add-data "gui_qt6:gui_qt6" \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=psutil \
    --hidden-import=sqlite3 \
    --hidden-import=xml.etree.ElementTree \
    --hidden-import=pathlib \
    --hidden-import=json \
    --hidden-import=uuid \
    --hidden-import=platform \
    --hidden-import=subprocess \
    --hidden-import=threading \
    --hidden-import=queue \
    --hidden-import=shutil \
    --hidden-import=tempfile \
    --collect-all=PyQt6 \
    --osx-bundle-identifier=com.basicprotein.augmentcode-free \
    --clean \
    main.py

# Set proper permissions on built files
echo "🔐 Setting permissions..."
if [ -f "dist/${APP_NAME}-v${VERSION}-macos-standalone" ]; then
    chmod +x "dist/${APP_NAME}-v${VERSION}-macos-standalone"
    echo "✅ Standalone executable built successfully"
fi

if [ -d "dist/${APP_NAME}-v${VERSION}-macos.app" ]; then
    chmod -R 755 "dist/${APP_NAME}-v${VERSION}-macos.app"
    echo "✅ App bundle built successfully"
fi

# Copy back to original directory
echo "📋 Copying builds back..."
cp -r dist/* "${OLDPWD}/dist/"

# Clean up
cd "${OLDPWD}"
rm -rf "${TEMP_DIR}"

echo "🎉 macOS build completed!"
echo "📁 Built files are in the dist/ directory"
echo ""
echo "📋 Usage instructions:"
echo "  Standalone: ./dist/${APP_NAME}-v${VERSION}-macos-standalone"
echo "  App bundle: open dist/${APP_NAME}-v${VERSION}-macos.app"
echo ""
echo "⚠️  If you get security warnings:"
echo "  1. Right-click the file and select 'Open'"
echo "  2. Or go to System Preferences > Security & Privacy > General"
echo "  3. Click 'Open Anyway' for the blocked application"
