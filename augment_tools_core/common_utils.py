"""
Common utility functions for Augment Tools Core
"""
import os
import platform
import shutil
import uuid
from pathlib import Path
from typing import Dict, Union, Optional
from enum import Enum

try:
    from colorama import init, Fore, Style
    init(autoreset=True)  # Initialize colorama for Windows support and auto-reset styles
    IS_COLORAMA_AVAILABLE = True
except ImportError:
    IS_COLORAMA_AVAILABLE = False

class IDEType(Enum):
    """Supported IDE types"""
    VSCODE = "vscode"
    CURSOR = "cursor"
    WINDSURF = "windsurf"
    JETBRAINS = "jetbrains"

# --- Console Message Functions ---
def print_message(prefix: str, message: str, color_code: str = "") -> None:
    """Helper function to print messages with optional color."""
    if IS_COLORAMA_AVAILABLE and color_code:
        print(f"{color_code}{prefix}{Style.RESET_ALL} {message}")
    else:
        print(f"{prefix} {message}")

def print_info(message: str) -> None:
    """Prints an informational message (blue if colorama is available)."""
    prefix = "[INFO]"
    color = Fore.BLUE if IS_COLORAMA_AVAILABLE else ""
    print_message(prefix, message, color)

def print_success(message: str) -> None:
    """Prints a success message (green if colorama is available)."""
    prefix = "[SUCCESS]"
    color = Fore.GREEN if IS_COLORAMA_AVAILABLE else ""
    print_message(prefix, message, color)

def print_warning(message: str) -> None:
    """Prints a warning message (yellow if colorama is available)."""
    prefix = "[WARNING]"
    color = Fore.YELLOW if IS_COLORAMA_AVAILABLE else ""
    print_message(prefix, message, color)

def print_error(message: str) -> None:
    """Prints an error message (red if colorama is available)."""
    prefix = "[ERROR]"
    color = Fore.RED if IS_COLORAMA_AVAILABLE else ""
    print_message(prefix, message, color)

# --- IDE Path Functions ---
def get_ide_paths(ide_type: IDEType) -> Optional[Dict[str, Path]]:
    """
    Determines and returns OS-specific paths for the specified IDE configuration files.

    Args:
        ide_type: The IDE type to get paths for

    Returns:
        A dictionary containing 'state_db' and 'storage_json' paths, or None if unsupported.
    """
    system = platform.system()
    paths: Dict[str, Path] = {}

    try:
        if ide_type == IDEType.VSCODE:
            if system == "Windows":
                appdata = os.environ.get("APPDATA")
                if not appdata:
                    print_error("APPDATA environment variable not found. Cannot locate VS Code data.")
                    return None
                base_dir = Path(appdata) / "Code" / "User"
            elif system == "Darwin":  # macOS
                base_dir = Path.home() / "Library" / "Application Support" / "Code" / "User"
            elif system == "Linux":
                base_dir = Path.home() / ".config" / "Code" / "User"
            else:
                print_error(f"Unsupported operating system: {system}")
                return None

            paths["state_db"] = base_dir / "globalStorage" / "state.vscdb"
            paths["storage_json"] = base_dir / "globalStorage" / "storage.json"

        elif ide_type == IDEType.CURSOR:
            if system == "Windows":
                appdata = os.environ.get("APPDATA")
                if not appdata:
                    print_error("APPDATA environment variable not found. Cannot locate Cursor data.")
                    return None
                base_dir = Path(appdata) / "Cursor" / "User"
            elif system == "Darwin":  # macOS
                # Cursor uses both locations based on your provided info
                base_dir = Path.home() / ".cursor"
                # Also check VS Code location for settings
                vscode_settings = Path.home() / "Library" / "Application Support" / "Code" / "User"
                paths["vscode_settings"] = vscode_settings / "settings.json"
            elif system == "Linux":
                base_dir = Path.home() / ".cursor"
            else:
                print_error(f"Unsupported operating system: {system}")
                return None

            # Cursor specific paths
            paths["state_db"] = base_dir / "globalStorage" / "state.vscdb"
            paths["storage_json"] = base_dir / "globalStorage" / "storage.json"
            paths["extensions"] = base_dir.parent / "extensions"

        elif ide_type == IDEType.WINDSURF:
            # Windsurf 可能有多种路径结构，需要检测实际存在的路径
            windsurf_paths = detect_windsurf_paths()
            if not windsurf_paths:
                print_error("无法找到 Windsurf 数据目录。请确保 Windsurf 已正确安装。")
                print_info("已检查标准路径和 Codeium 路径，详细信息请查看上方输出。")
                return None

            paths.update(windsurf_paths)

        elif ide_type == IDEType.JETBRAINS:
            # JetBrains 产品使用不同的配置结构，不需要传统的 state_db 和 storage_json
            # 返回空字典表示支持但使用不同的处理方式
            print_info("JetBrains 产品使用 SessionID 配置，不需要数据库清理")
            return {}

        return paths
    except Exception as e:
        print_error(f"Failed to determine {ide_type.value} paths: {e}")
        return None

def detect_windsurf_paths() -> Dict[str, Path]:
    """
    检测 Windsurf 的实际数据路径。
    支持两种路径结构：
    1. 标准 VSCode 结构：%APPDATA%/Windsurf/ 或 ~/.config/Windsurf/
    2. Codeium 结构：~/.codeium/windsurf/

    Returns:
        包含实际存在路径的字典，如果未找到则返回空字典
    """
    import platform

    home = Path.home()
    system = platform.system()

    # 构建标准路径
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            standard_base = Path(appdata) / "Windsurf"
        else:
            standard_base = None
    elif system == "Darwin":  # macOS
        standard_base = home / "Library" / "Application Support" / "Windsurf"
    else:  # Linux
        standard_base = home / ".config" / "Windsurf"

    # 所有可能的基础目录（按优先级排序）
    possible_base_dirs = []

    # 1. 标准路径（优先级最高）
    if standard_base:
        possible_base_dirs.append(standard_base)

    # 2. Codeium 路径
    possible_base_dirs.extend([
        home / ".codeium" / "windsurf",
        home / ".windsurf",
        home / ".codeium" / "windsurf" / "User",
    ])

    # 可能的子目录结构（按优先级排序）
    possible_structures = [
        # 标准 VSCode 结构（最高优先级）
        ("User/globalStorage", "extensions"),
        ("User/globalStorage", "User/extensions"),
        # Codeium 可能的结构
        ("globalStorage", "extensions"),
        ("data/User/globalStorage", "data/extensions"),
    ]

    for base_dir in possible_base_dirs:
        if not base_dir.exists():
            continue

        # 判断路径类型以便更好的调试信息
        if "Windsurf" in str(base_dir) and ("AppData" in str(base_dir) or "Application Support" in str(base_dir) or ".config" in str(base_dir)):
            path_type = "标准路径"
        elif ".codeium" in str(base_dir):
            path_type = "Codeium路径"
        else:
            path_type = "其他路径"

        print_info(f"检查 Windsurf {path_type}: {base_dir}")

        for storage_path, ext_path in possible_structures:
            state_db = base_dir / storage_path / "state.vscdb"
            storage_json = base_dir / storage_path / "storage.json"
            extensions = base_dir / ext_path

            # 检查关键文件是否存在
            if state_db.exists() or storage_json.exists():
                print_success(f"✅ 找到 Windsurf 数据目录 ({path_type}): {base_dir}")
                print_info(f"  - 数据库路径: {state_db} {'✅' if state_db.exists() else '❌'}")
                print_info(f"  - 存储文件路径: {storage_json} {'✅' if storage_json.exists() else '❌'}")
                print_info(f"  - 扩展目录: {extensions}")

                return {
                    "state_db": state_db,
                    "storage_json": storage_json,
                    "extensions": extensions
                }

    # 如果没有找到，列出实际存在的目录以帮助调试
    print_warning("❌ 未找到 Windsurf 数据文件。")
    print_info("📋 检查的路径结构:")
    print_info("  标准路径:")
    if standard_base:
        if standard_base.exists():
            print_info(f"    ✅ 存在: {standard_base}")
            try:
                for item in standard_base.iterdir():
                    if item.is_dir():
                        print_info(f"      子目录: {item.name}")
            except PermissionError:
                print_warning(f"      无法访问目录内容 (权限不足)")
        else:
            print_info(f"    ❌ 不存在: {standard_base}")

    print_info("  Codeium路径:")
    for base_dir in possible_base_dirs[1:]:  # 跳过标准路径
        if base_dir.exists():
            print_info(f"    ✅ 存在: {base_dir}")
            try:
                for item in base_dir.iterdir():
                    if item.is_dir():
                        print_info(f"      子目录: {item.name}")
            except PermissionError:
                print_warning(f"      无法访问目录内容 (权限不足)")
        else:
            print_info(f"    ❌ 不存在: {base_dir}")

    return {}

def get_os_specific_vscode_paths() -> Dict[str, Path]:
    """
    Legacy function for backward compatibility.
    Determines and returns OS-specific paths for VS Code configuration files.
    """
    paths = get_ide_paths(IDEType.VSCODE)
    if not paths:
        raise SystemExit(1)
    return paths

def get_ide_display_name(ide_type: IDEType) -> str:
    """Get display name for IDE type"""
    display_names = {
        IDEType.VSCODE: "VS Code",
        IDEType.CURSOR: "Cursor",
        IDEType.WINDSURF: "Windsurf",
        IDEType.JETBRAINS: "JetBrains"
    }
    return display_names.get(ide_type, ide_type.value)

def get_ide_process_names(ide_type: IDEType) -> list:
    """Get process names for the specified IDE"""
    process_names = {
        IDEType.VSCODE: ["Code.exe", "Code - Insiders.exe", "Code - OSS.exe"],
        IDEType.CURSOR: ["Cursor.exe", "cursor.exe"],
        IDEType.WINDSURF: ["Windsurf.exe", "windsurf.exe"],
        IDEType.JETBRAINS: [
            "pycharm64.exe", "pycharm.exe", "idea64.exe", "idea.exe",
            "webstorm64.exe", "webstorm.exe", "phpstorm64.exe", "phpstorm.exe",
            "clion64.exe", "clion.exe", "datagrip64.exe", "datagrip.exe",
            "goland64.exe", "goland.exe", "rubymine64.exe", "rubymine.exe",
            "rider64.exe", "rider.exe", "dataspell64.exe", "dataspell.exe"
        ]
    }
    return process_names.get(ide_type, [])

# --- File Backup Function ---
def create_backup(file_path: Union[str, Path]) -> Union[Path, None]:
    """
    Creates a backup of the given file.

    Args:
        file_path: The path to the file to be backed up.

    Returns:
        The path to the backup file if successful, None otherwise.
    """
    original_path = Path(file_path)
    if not original_path.exists():
        print_error(f"File not found for backup: {original_path}")
        return None

    backup_path = original_path.with_suffix(original_path.suffix + ".backup")
    try:
        shutil.copy2(original_path, backup_path)
        print_success(f"Backup created successfully at: {backup_path}")
        return backup_path
    except Exception as e:
        print_error(f"Failed to create backup for {original_path}: {e}")
        return None

# --- ID Generation Functions ---
def generate_new_machine_id() -> str:
    """Generates a new 64-character hexadecimal string for machineId."""
    return uuid.uuid4().hex + uuid.uuid4().hex

def generate_new_device_id() -> str:
    """Generates a new standard UUID v4 string for devDeviceId."""
    return str(uuid.uuid4())

if __name__ == '__main__':
    # Quick test for the utility functions
    print_info("Testing common_utils.py...")

    print_info("Displaying detected VS Code paths:")
    try:
        vscode_paths = get_os_specific_vscode_paths()
        print_success(f"  State DB: {vscode_paths['state_db']}")
        print_success(f"  Storage JSON: {vscode_paths['storage_json']}")
    except SystemExit:
        print_warning("Could not retrieve VS Code paths on this system (expected if run in isolated env).")


    print_info("Generating sample IDs:")
    machine_id = generate_new_machine_id()
    device_id = generate_new_device_id()
    print_success(f"  Generated Machine ID: {machine_id} (Length: {len(machine_id)})")
    print_success(f"  Generated Device ID: {device_id}")

    # To test backup, you'd need a dummy file.
    # Example:
    # test_file = Path("dummy_test_file.txt")
    # with open(test_file, "w") as f:
    #     f.write("This is a test file for backup.")
    # backup_result = create_backup(test_file)
    # if backup_result:
    #     print_info(f"Backup test successful. Backup at: {backup_result}")
    #     if backup_result.exists():
    #         backup_result.unlink() # Clean up backup
    # if test_file.exists():
    #     test_file.unlink() # Clean up test file

    print_info("Testing message types:")
    print_success("This is a success message.")
    print_warning("This is a warning message.")
    print_error("This is an error message.")
    print_info("common_utils.py tests complete.")

# === 新增功能：进程和文件管理工具函数 ===

def is_process_running(process_name: str) -> bool:
    """
    检查指定名称的进程是否在运行

    Args:
        process_name: 进程名称

    Returns:
        bool: 是否在运行
    """
    try:
        import subprocess
        import platform

        system = platform.system()
        if system == "Windows":
            cmd = f'tasklist /FI "IMAGENAME eq {process_name}" /FO CSV'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk', errors='ignore')
            return process_name.lower() in result.stdout.lower()
        else:
            search_pattern = process_name.replace('.exe', '')
            cmd = f'pgrep -f "{search_pattern}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
    except Exception:
        return False

def get_file_size_mb(file_path: Path) -> float:
    """
    获取文件大小（MB）

    Args:
        file_path: 文件路径

    Returns:
        float: 文件大小（MB），如果文件不存在返回0
    """
    try:
        if file_path.exists():
            size_bytes = file_path.stat().st_size
            return size_bytes / (1024 * 1024)
        return 0.0
    except Exception:
        return 0.0

def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示

    Args:
        size_bytes: 字节数

    Returns:
        str: 格式化的大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def safe_remove_file(file_path: Path, max_retries: int = 3) -> bool:
    """
    安全删除文件（带重试）

    Args:
        file_path: 文件路径
        max_retries: 最大重试次数

    Returns:
        bool: 是否成功删除
    """
    import time

    if not file_path.exists():
        return True

    for attempt in range(max_retries):
        try:
            file_path.unlink()
            return True
        except (PermissionError, OSError) as e:
            if attempt < max_retries - 1:
                print_warning(f"删除文件失败，重试中... ({attempt + 1}/{max_retries})")
                time.sleep(1)
            else:
                print_error(f"删除文件失败: {file_path} - {e}")
                return False
        except Exception as e:
            print_error(f"删除文件时发生意外错误: {file_path} - {e}")
            return False

    return False

def get_cleanup_mode_display_name(mode: str) -> str:
    """
    获取清理模式的显示名称

    Args:
        mode: 清理模式字符串

    Returns:
        str: 显示名称
    """
    mode_names = {
        "database_only": "仅数据库清理",
        "file_only": "仅文件删除",
        "hybrid": "混合模式",
        "aggressive": "激进模式"
    }
    return mode_names.get(mode, mode)

def validate_cleanup_options(mode: str, ide_type: IDEType) -> tuple[bool, str]:
    """
    验证清理选项的有效性

    Args:
        mode: 清理模式
        ide_type: IDE类型

    Returns:
        tuple[bool, str]: (是否有效, 错误信息)
    """
    valid_modes = ["database_only", "file_only", "hybrid", "aggressive"]

    if mode not in valid_modes:
        return False, f"无效的清理模式: {mode}。有效模式: {', '.join(valid_modes)}"

    # JetBrains产品只支持特定模式
    if ide_type == IDEType.JETBRAINS and mode in ["file_only", "aggressive"]:
        return False, f"JetBrains产品不支持 {mode} 模式"

    return True, ""

def get_ide_process_names(ide_type: IDEType) -> list[str]:
    """
    获取IDE的进程名称列表

    Args:
        ide_type: IDE类型

    Returns:
        list[str]: 进程名称列表
    """
    process_names = {
        IDEType.VSCODE: ['Code.exe', 'Code - Insiders.exe', 'Code - OSS.exe'],
        IDEType.CURSOR: ['Cursor.exe', 'cursor.exe'],
        IDEType.WINDSURF: ['Windsurf.exe', 'windsurf.exe'],
        IDEType.JETBRAINS: [
            'idea64.exe', 'idea.exe', 'pycharm64.exe', 'pycharm.exe',
            'webstorm64.exe', 'webstorm.exe', 'phpstorm64.exe', 'phpstorm.exe'
        ]
    }
    return process_names.get(ide_type, [])


# --- Patch Related Functions ---
def get_ide_extension_name(ide_type: IDEType) -> str:
    """Get the extension name pattern for the specified IDE"""
    extension_names = {
        IDEType.VSCODE: "augment.vscode-augment",
        IDEType.CURSOR: "augment.cursor-augment",
        IDEType.WINDSURF: "augment.windsurf-augment",
        IDEType.JETBRAINS: "augment.jetbrains-augment"
    }
    return extension_names.get(ide_type, "augment")


def get_patch_target_description(ide_type: IDEType) -> str:
    """Get description of what will be patched for the IDE"""
    descriptions = {
        IDEType.VSCODE: "VS Code AugmentCode 扩展文件",
        IDEType.CURSOR: "Cursor AugmentCode 扩展文件",
        IDEType.WINDSURF: "Windsurf AugmentCode 扩展文件",
        IDEType.JETBRAINS: "JetBrains AugmentCode 插件文件"
    }
    return descriptions.get(ide_type, f"{ide_type.value} 扩展文件")
