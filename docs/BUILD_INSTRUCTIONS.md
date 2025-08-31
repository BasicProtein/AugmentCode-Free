# AugmentCode-Free v2.0.4 构建说明 / Build Instructions

## Windows 平台 / Windows Platform ✅

### 自动构建 / Automated Build

使用 GitHub Actions 自动构建 / Use GitHub Actions for automated builds:

```bash
# 触发构建 / Trigger build
git tag v2.0.4
git push origin v2.0.4
```

### 手动构建 / Manual Build

```bash
# 安装依赖 / Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# 构建可执行文件 / Build executable
pyinstaller --onefile --windowed \
    --name "AugmentCode-Free-v2.0.4-windows" \
    --add-data "languages;languages" \
    --add-data "config;config" \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=psutil \
    --collect-all=PyQt6 \
    main.py
```

**构建产物 / Build Artifacts:**
- `AugmentCode-Free-v2.0.4-windows.exe` - Windows 可执行文件 / Windows executable

## macOS 平台构建 / macOS Platform Build

### 🚨 macOS 构建问题修复 / macOS Build Issues Fixed

**常见问题 / Common Issues:**
- `Failed to create parent directory structure` 错误
- 权限问题导致的构建失败
- 应用无法启动或闪退

**解决方案 / Solutions:**

#### 方法一：使用自动构建脚本 / Method 1: Use Automated Build Script

```bash
# 使用提供的构建脚本（推荐）/ Use provided build script (recommended)
chmod +x build_macos.sh
./build_macos.sh
```

#### 方法二：手动构建 / Method 2: Manual Build

```bash
# 安装依赖 / Install dependencies
pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 install pyinstaller

# 清理之前的构建 / Clean previous builds
rm -rf build/ dist/ *.spec

# 构建独立可执行文件（推荐，兼容性更好）/ Build standalone executable (recommended, better compatibility)
pyinstaller --onefile \
    --name AugmentCode-Free-v2.0.4-macos-standalone \
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

# 构建应用包 / Build app bundle
pyinstaller --onefile --windowed \
    --name AugmentCode-Free-v2.0.4-macos \
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

# 设置权限 / Set permissions
chmod +x dist/AugmentCode-Free-v2.0.4-macos-standalone
chmod -R 755 dist/AugmentCode-Free-v2.0.4-macos.app

```

#### 运行说明 / Running Instructions

**独立可执行文件 / Standalone Executable:**
```bash
# 运行独立可执行文件 / Run standalone executable
./dist/AugmentCode-Free-v2.0.4-macos-standalone
```

**应用包 / App Bundle:**
```bash
# 运行应用包 / Run app bundle
open dist/AugmentCode-Free-v2.0.4-macos.app
```

#### 安全设置 / Security Settings

如果遇到安全警告 / If you encounter security warnings:

1. **右键打开 / Right-click to open:**
   - 右键点击应用 → 选择"打开"
   - Right-click the app → Select "Open"

2. **系统偏好设置 / System Preferences:**
   - 系统偏好设置 → 安全性与隐私 → 通用
   - System Preferences → Security & Privacy → General
   - 点击"仍要打开" / Click "Open Anyway"

3. **终端授权 / Terminal Authorization:**
   ```bash
   # 移除隔离属性 / Remove quarantine attribute
   xattr -d com.apple.quarantine dist/AugmentCode-Free-v2.0.4-macos-standalone
   xattr -rd com.apple.quarantine dist/AugmentCode-Free-v2.0.4-macos.app
   ```

#### 创建 DMG 包（可选）/ Create DMG package (optional)
```bash
# 需要安装 create-dmg: brew install create-dmg
# Requires create-dmg: brew install create-dmg
create-dmg \
    --volname "AugmentCode-Free v2.0.4" \
    --window-pos 200 120 \
    --window-size 600 300 \
    --icon-size 100 \
    --icon "AugmentCode-Free-v2.0.4-macos.app" 175 120 \
    --hide-extension "AugmentCode-Free-v2.0.4-macos.app" \
    --app-drop-link 425 120 \
    "AugmentCode-Free-v2.0.4.dmg" \
    "dist/"
```

## Linux 平台构建 / Linux Platform Build

### 自动构建 / Automated Build

使用 GitHub Actions 自动构建 / Use GitHub Actions for automated builds:

```bash
# 触发构建 / Trigger build
git tag v2.0.4
git push origin v2.0.4
```

### 手动构建 / Manual Build

在 Linux 系统上执行以下命令 / Execute the following commands on Linux:

```bash
# 安装系统依赖（Ubuntu/Debian）/ Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    libgl1-mesa-glx libegl1-mesa \
    libxrandr2 libxss1 libxcursor1 \
    libxcomposite1 libasound2 libxi6 \
    libxtst6 libglib2.0-0 libgtk-3-0

# 创建虚拟环境 / Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖 / Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 构建 Linux 可执行文件 / Build Linux executable
pyinstaller --onefile \
    --name "AugmentCode-Free-v2.0.4-linux" \
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
    --collect-all=PyQt6 \
    main.py

# 设置执行权限 / Set execution permissions
chmod +x dist/AugmentCode-Free-v2.0.4-linux

# 创建 AppImage（可选）/ Create AppImage (optional)
# 需要下载 appimagetool / Download appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# 创建 AppDir 结构 / Create AppDir structure
mkdir -p AugmentCode-Free.AppDir/usr/bin
mkdir -p AugmentCode-Free.AppDir/usr/share/applications
mkdir -p AugmentCode-Free.AppDir/usr/share/icons/hicolor/256x256/apps

# 复制可执行文件 / Copy executable
cp dist/AugmentCode-Free-v1.0.6 AugmentCode-Free.AppDir/usr/bin/

# 创建 .desktop 文件 / Create .desktop file
cat > AugmentCode-Free.AppDir/AugmentCode-Free.desktop << EOF
[Desktop Entry]
Type=Application
Name=AugmentCode-Free
Exec=AugmentCode-Free-v1.0.6
Icon=augmentcode-free
Categories=Development;
EOF

# 创建 AppRun 脚本 / Create AppRun script
cat > AugmentCode-Free.AppDir/AppRun << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
exec ./usr/bin/AugmentCode-Free-v1.0.6 "\$@"
EOF
chmod +x AugmentCode-Free.AppDir/AppRun

# 构建 AppImage / Build AppImage
./appimagetool-x86_64.AppImage AugmentCode-Free.AppDir AugmentCode-Free-v1.0.6-x86_64.AppImage
```

## 构建验证 / Build Verification

构建完成后，请验证以下功能 / After building, please verify the following functions:

1. **启动测试 / Startup Test**: 程序能正常启动并显示GUI / Program starts normally and displays GUI
2. **IDE检测 / IDE Detection**: 能正确检测已安装的IDE / Correctly detects installed IDEs
3. **功能测试 / Function Test**:
   - VS Code/Cursor/Windsurf 数据库清理 / Database cleaning
   - 遥测ID修改 / Telemetry ID modification
   - JetBrains SessionID修改 / JetBrains SessionID modification
   - 代码补丁应用和恢复 / Code patch application and restoration
4. **权限检查 / Permission Check**: 文件权限检查和错误提示正常工作 / File permission check and error messages work properly
5. **多语言 / Multi-language**: 中英文界面切换正常 / Chinese/English interface switching works properly
6. **进程检测 / Process Detection**: 能正确检测运行中的IDE进程 / Correctly detects running IDE processes

## 预期输出文件 / Expected Output Files

构建成功后，您应该在 `dist/` 目录中找到以下文件 / After successful build, you should find the following files in the `dist/` directory:

- **Windows**:
  - `AugmentCode-Free-v2.0.4-windows.exe` (约 35-40 MB / approximately 35-40 MB)

- **macOS**:
  - `AugmentCode-Free-v2.0.4-macos.app` (应用包 / app bundle)
  - `AugmentCode-Free-v2.0.4-macos-standalone` (独立可执行文件 / standalone executable)

- **Linux**:
  - `AugmentCode-Free-v2.0.4-linux` (可执行文件 / executable)

## 故障排除 / Troubleshooting

### 通用问题 / Common Issues

1. **依赖缺失 / Missing Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **权限问题 / Permission Issues**:
   ```bash
   # Linux/macOS
   chmod +x dist/AugmentCode-Free-v2.0.4-*

   # macOS 特殊处理 / macOS special handling
   xattr -d com.apple.quarantine dist/AugmentCode-Free-v2.0.4-macos*
   ```

3. **构建失败 / Build Failure**:
   - 清理之前的构建 / Clean previous builds: `rm -rf build/ dist/ *.spec`
   - 检查 Python 版本 / Check Python version: `python --version` (需要 3.7+ / requires 3.7+)
   - 检查依赖版本 / Check dependency versions: `pip list`

### macOS 特殊问题 / macOS Specific Issues

请参考详细的 [macOS 故障排除指南](https://github.com/BasicProtein/AugmentCode-Free/blob/main/docs/MACOS_TROUBLESHOOTING.md) / Please refer to the detailed [macOS Troubleshooting Guide](https://github.com/BasicProtein/AugmentCode-Free/blob/main/docs/MACOS_TROUBLESHOOTING.md)

### 获取帮助 / Getting Help

如果遇到构建问题，请在 GitHub 上创建 Issue 并提供：
If you encounter build issues, please create an Issue on GitHub and provide:

- 操作系统和版本 / Operating system and version
- Python 版本 / Python version
- 完整的错误信息 / Complete error message
- 使用的构建命令 / Build commands used

**GitHub Issues**: https://github.com/BasicProtein/AugmentCode-Free/issues

## 注意事项 / Important Notes

1. **依赖管理 / Dependency Management**: 确保所有平台都包含必要的系统依赖 / Ensure all platforms include necessary system dependencies
2. **权限设置 / Permission Settings**: Linux/macOS 可执行文件需要执行权限 / Linux/macOS executables need execute permissions
3. **代码签名 / Code Signing**: macOS 可能需要代码签名以避免安全警告 / macOS may require code signing to avoid security warnings
4. **测试环境 / Testing Environment**: 在干净的系统上测试以确保依赖完整性 / Test on clean systems to ensure dependency integrity
