# macOS 故障排除指南 / macOS Troubleshooting Guide

## 🚨 常见问题与解决方案 / Common Issues and Solutions

### 问题 1: "Failed to create parent directory structure"

**症状 / Symptoms:**
```
[PYI-44086:ERROR] Failed to create parent directory structure.
```

**原因 / Causes:**
- PyInstaller 权限问题
- 临时目录权限不足
- 路径包含特殊字符

**解决方案 / Solutions:**

#### 方案 A: 使用自动构建脚本
```bash
# 下载并运行自动构建脚本
chmod +x build_macos.sh
./build_macos.sh
```

#### 方案 B: 手动修复权限
```bash
# 1. 清理之前的构建
rm -rf build/ dist/ *.spec

# 2. 创建临时目录并设置权限
TEMP_DIR=$(mktemp -d)
cp -r . "$TEMP_DIR/"
cd "$TEMP_DIR"
chmod -R 755 .

# 3. 重新构建
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
    --collect-all=PyQt6 \
    --target-arch=universal2 \
    --clean \
    main.py

# 4. 复制回原目录
cp -r dist/* "$OLDPWD/dist/"
cd "$OLDPWD"
rm -rf "$TEMP_DIR"
```

### 问题 2: 应用无法启动或闪退

**症状 / Symptoms:**
- 双击 .app 文件无反应
- 应用启动后立即退出
- 终端运行显示权限错误

**解决方案 / Solutions:**

#### 方案 A: 移除隔离属性
```bash
# 移除 macOS 隔离属性
xattr -d com.apple.quarantine dist/AugmentCode-Free-v2.0.4-macos.app
xattr -d com.apple.quarantine dist/AugmentCode-Free-v2.0.4-macos-standalone

# 设置执行权限
chmod +x dist/AugmentCode-Free-v2.0.4-macos-standalone
chmod -R 755 dist/AugmentCode-Free-v2.0.4-macos.app
```

#### 方案 B: 使用独立可执行文件
```bash
# 推荐使用独立可执行文件而不是 .app 包
./dist/AugmentCode-Free-v2.0.4-macos-standalone
```

### 问题 3: 安全警告

**症状 / Symptoms:**
- "无法打开，因为它来自身份不明的开发者"
- "已损坏，无法打开"

**解决方案 / Solutions:**

#### 方案 A: 右键打开
1. 右键点击应用文件
2. 选择"打开"
3. 在弹出的对话框中点击"打开"

#### 方案 B: 系统偏好设置
1. 打开"系统偏好设置"
2. 选择"安全性与隐私"
3. 在"通用"标签页中点击"仍要打开"

#### 方案 C: 终端命令
```bash
# 临时允许运行
sudo spctl --master-disable

# 运行应用后重新启用保护
sudo spctl --master-enable
```

### 问题 4: 缺少依赖

**症状 / Symptoms:**
- 导入错误
- 模块未找到

**解决方案 / Solutions:**

```bash
# 确保所有依赖已安装
pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 install pyinstaller

# 重新构建时添加更多隐藏导入
pyinstaller --onefile \
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
    main.py
```

## 🔧 调试技巧 / Debugging Tips

### 1. 查看详细错误信息
```bash
# 在终端中运行以查看详细错误
./dist/AugmentCode-Free-v2.0.4-macos-standalone --debug
```

### 2. 检查文件权限
```bash
# 检查文件权限
ls -la dist/
```

### 3. 查看隔离属性
```bash
# 检查是否有隔离属性
xattr -l dist/AugmentCode-Free-v2.0.4-macos-standalone
```

### 4. 测试 Python 环境
```bash
# 测试 Python 环境
python3 -c "import PyQt6; print('PyQt6 OK')"
python3 -c "import psutil; print('psutil OK')"
```

## 📞 获取帮助 / Getting Help

如果以上解决方案都无法解决问题，请：

1. 在 GitHub 上创建 Issue
2. 提供以下信息：
   - macOS 版本
   - Python 版本
   - 完整的错误信息
   - 使用的构建命令

**GitHub Issues:** https://github.com/BasicProtein/AugmentCode-Free/issues

---

# macOS Troubleshooting Guide / macOS 故障排除指南

## 🚨 Common Issues and Solutions / 常见问题与解决方案

### Issue 1: "Failed to create parent directory structure"

**Symptoms / 症状:**
```
[PYI-44086:ERROR] Failed to create parent directory structure.
```

**Causes / 原因:**
- PyInstaller permission issues / PyInstaller 权限问题
- Insufficient temporary directory permissions / 临时目录权限不足
- Path contains special characters / 路径包含特殊字符

**Solutions / 解决方案:**

#### Solution A: Use Automated Build Script / 方案 A: 使用自动构建脚本
```bash
# Download and run automated build script / 下载并运行自动构建脚本
chmod +x build_macos.sh
./build_macos.sh
```

#### Solution B: Manual Permission Fix / 方案 B: 手动修复权限
```bash
# 1. Clean previous builds / 清理之前的构建
rm -rf build/ dist/ *.spec

# 2. Create temporary directory and set permissions / 创建临时目录并设置权限
TEMP_DIR=$(mktemp -d)
cp -r . "$TEMP_DIR/"
cd "$TEMP_DIR"
chmod -R 755 .

# 3. Rebuild / 重新构建
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
    --collect-all=PyQt6 \
    --target-arch=universal2 \
    --clean \
    main.py

# 4. Copy back to original directory / 复制回原目录
cp -r dist/* "$OLDPWD/dist/"
cd "$OLDPWD"
rm -rf "$TEMP_DIR"
```

### Issue 2: Application Won't Start or Crashes / 问题 2: 应用无法启动或闪退

**Symptoms / 症状:**
- Double-clicking .app file has no effect / 双击 .app 文件无反应
- Application exits immediately after startup / 应用启动后立即退出
- Terminal shows permission errors / 终端运行显示权限错误

**Solutions / 解决方案:**

#### Solution A: Remove Quarantine Attributes / 方案 A: 移除隔离属性
```bash
# Remove macOS quarantine attributes / 移除 macOS 隔离属性
xattr -d com.apple.quarantine dist/AugmentCode-Free-v2.0.4-macos.app
xattr -d com.apple.quarantine dist/AugmentCode-Free-v2.0.4-macos-standalone

# Set execution permissions / 设置执行权限
chmod +x dist/AugmentCode-Free-v2.0.4-macos-standalone
chmod -R 755 dist/AugmentCode-Free-v2.0.4-macos.app
```

#### Solution B: Use Standalone Executable / 方案 B: 使用独立可执行文件
```bash
# Recommended: use standalone executable instead of .app bundle / 推荐使用独立可执行文件而不是 .app 包
./dist/AugmentCode-Free-v2.0.4-macos-standalone
```

### Issue 3: Security Warnings / 问题 3: 安全警告

**Symptoms / 症状:**
- "Cannot open because it's from an unidentified developer" / "无法打开，因为它来自身份不明的开发者"
- "Damaged and can't be opened" / "已损坏，无法打开"

**Solutions / 解决方案:**

#### Solution A: Right-click to Open / 方案 A: 右键打开
1. Right-click the application file / 右键点击应用文件
2. Select "Open" / 选择"打开"
3. Click "Open" in the popup dialog / 在弹出的对话框中点击"打开"

#### Solution B: System Preferences / 方案 B: 系统偏好设置
1. Open "System Preferences" / 打开"系统偏好设置"
2. Select "Security & Privacy" / 选择"安全性与隐私"
3. Click "Open Anyway" in the "General" tab / 在"通用"标签页中点击"仍要打开"

#### Solution C: Terminal Commands / 方案 C: 终端命令
```bash
# Temporarily allow execution / 临时允许运行
sudo spctl --master-disable

# Re-enable protection after running the app / 运行应用后重新启用保护
sudo spctl --master-enable
```

## 🔧 Debugging Tips / 调试技巧

### 1. View Detailed Error Information / 查看详细错误信息
```bash
# Run in terminal to see detailed errors / 在终端中运行以查看详细错误
./dist/AugmentCode-Free-v2.0.4-macos-standalone --debug
```

### 2. Check File Permissions / 检查文件权限
```bash
# Check file permissions / 检查文件权限
ls -la dist/
```

### 3. View Quarantine Attributes / 查看隔离属性
```bash
# Check for quarantine attributes / 检查是否有隔离属性
xattr -l dist/AugmentCode-Free-v2.0.4-macos-standalone
```

### 4. Test Python Environment / 测试 Python 环境
```bash
# Test Python environment / 测试 Python 环境
python3 -c "import PyQt6; print('PyQt6 OK')"
python3 -c "import psutil; print('psutil OK')"
```

## 📞 Getting Help / 获取帮助

If none of the above solutions work, please: / 如果以上解决方案都无法解决问题，请：

1. Create an Issue on GitHub / 在 GitHub 上创建 Issue
2. Provide the following information / 提供以下信息：
   - macOS version / macOS 版本
   - Python version / Python 版本
   - Complete error message / 完整的错误信息
   - Build commands used / 使用的构建命令

**GitHub Issues:** https://github.com/BasicProtein/AugmentCode-Free/issues
