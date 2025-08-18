## 📦 Installation Method

### Local VSIX Installation Package

**Important Note**: This is a local installation package that requires manual download and installation. It cannot be installed directly through the VSCode Extension Marketplace.

#### Method 1: GUI Installation (Recommended, Suitable for General Users)

1.  Visit the [Releases page](https://github.com/agassiz/vscode-augment/releases).
2.  Download the latest version `v0.521.1-25-0805`.
3.  Open VSCode and click the extension icon on the left (or press `Ctrl+Shift+X` / `Cmd+Shift+X`).
4.  Click the `...` (More Actions) button in the top-right corner of the extension panel.
5.  Select `Install from VSIX...`.
6.  Browse and select the downloaded `.vsix` file.
7.  **Important**: You must restart VSCode after the installation is complete.

#### Method 2: Command Palette Installation

1.  After downloading the `.vsix` file, press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS).
2.  Enter `Extensions: Install from VSIX...`.
3.  Select the downloaded `.vsix` file to install.
4.  **Important**: You must restart VSCode after installation.

#### Method 3: Command Line Installation (for Developers)

After downloading the `.vsix` file, execute the following command in the directory:

```bash
code --install-extension vscode-augment-0.521.1.vsix
```

#### Method 4: Drag-and-Drop Installation (Easiest)

1.  Download the `.vsix` file to your local computer.
2.  Open the VSCode Extensions panel (`Ctrl+Shift+X` / `Cmd+Shift+X`).
3.  Drag the `.vsix` file directly into the Extensions panel.
4.  Confirm installation and restart VSCode.

> **💡 Installation Tips**: We recommend using Method 1 (GUI) or Method 4 (drag-and-drop). These two methods are the most user-friendly and do not require command-line access.

## 🚀 Instructions

Features of the Local Installation Package:

  - This is a modified local installation package that does not rely on the official extension store.
  - After installation, you must restart VS Code for normal use.
  - Functionality is identical to the official version, except that some risk control code has been removed.

After installation, the plugin will automatically activate. You can use it in the following ways:

1.  **Function Access**: Search for related commands in the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
2.  **Shortcuts**: View the shortcut configuration in the extension settings.
3.  **Settings**: Search for `augment` in the VSCode settings to customize it.

## ⚙️ Configuration Options

The extension provides a wealth of configuration options, which you can adjust in the VSCode settings:

  - Open settings: `File` \> `Preferences` \> `Settings` (Windows/Linux) or `Code` \> `Preferences` \> `Settings` (macOS).
  - Search for `augment` to view all configurable options.

## 🔧 Development Environment

  - **VSCode Version Requirement**: `>= 1.60.0`
  - **Node.js Version**: `>= 14.0.0`
