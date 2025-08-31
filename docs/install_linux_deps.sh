#!/bin/bash
# Linux 系统依赖安装脚本
# 用于解决 Qt6 平台插件错误

echo "🔧 AugmentCode-Free Linux 依赖安装脚本"
echo "=========================================="

# 检测 Linux 发行版
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
elif type lsb_release >/dev/null 2>&1; then
    OS=$(lsb_release -si)
    VER=$(lsb_release -sr)
elif [ -f /etc/lsb-release ]; then
    . /etc/lsb-release
    OS=$DISTRIB_ID
    VER=$DISTRIB_RELEASE
elif [ -f /etc/debian_version ]; then
    OS=Debian
    VER=$(cat /etc/debian_version)
elif [ -f /etc/SuSe-release ]; then
    OS=openSUSE
elif [ -f /etc/redhat-release ]; then
    OS=RedHat
else
    OS=$(uname -s)
    VER=$(uname -r)
fi

echo "检测到系统: $OS $VER"
echo ""

# 根据发行版安装依赖
case "$OS" in
    *Ubuntu*|*Debian*)
        echo "📦 安装 Ubuntu/Debian Qt6 依赖..."
        sudo apt update
        sudo apt install -y \
            libxcb-xinerama0 \
            libxcb-cursor0 \
            libxcb-icccm4 \
            libxcb-image0 \
            libxcb-keysyms1 \
            libxcb-render-util0 \
            libxcb-shape0 \
            libxcb-util1 \
            libxcb-xkb1 \
            libxkbcommon-x11-0 \
            python3-pip \
            python3-venv
        ;;
    *CentOS*|*Red\ Hat*|*RHEL*)
        echo "📦 安装 CentOS/RHEL Qt6 依赖..."
        sudo yum install -y \
            libxcb-devel \
            xcb-util-devel \
            xcb-util-cursor-devel \
            xcb-util-keysyms-devel \
            xcb-util-image-devel \
            xcb-util-wm-devel \
            xcb-util-renderutil-devel \
            python3-pip
        ;;
    *Fedora*)
        echo "📦 安装 Fedora Qt6 依赖..."
        sudo dnf install -y \
            libxcb-devel \
            xcb-util-devel \
            xcb-util-cursor-devel \
            xcb-util-keysyms-devel \
            xcb-util-image-devel \
            xcb-util-wm-devel \
            xcb-util-renderutil-devel \
            python3-pip
        ;;
    *Arch*)
        echo "📦 安装 Arch Linux Qt6 依赖..."
        sudo pacman -S --noconfirm \
            libxcb \
            xcb-util \
            xcb-util-cursor \
            xcb-util-keysyms \
            xcb-util-image \
            xcb-util-wm \
            xcb-util-renderutil \
            python-pip
        ;;
    *openSUSE*)
        echo "📦 安装 openSUSE Qt6 依赖..."
        sudo zypper install -y \
            libxcb-devel \
            xcb-util-devel \
            xcb-util-cursor-devel \
            xcb-util-keysyms-devel \
            xcb-util-image-devel \
            xcb-util-wm-devel \
            xcb-util-renderutil-devel \
            python3-pip
        ;;
    *)
        echo "❌ 不支持的 Linux 发行版: $OS"
        echo "请手动安装以下包的等效版本:"
        echo "  - libxcb 相关包"
        echo "  - xcb-util 相关包"
        echo "  - python3-pip"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 系统依赖安装完成！"
    echo ""
    echo "📋 接下来的步骤:"
    echo "1. 安装 Python 依赖: pip install -r requirements.txt"
    echo "2. 运行程序: python main.py"
    echo ""
else
    echo ""
    echo "❌ 依赖安装失败，请检查错误信息并手动安装"
    exit 1
fi
