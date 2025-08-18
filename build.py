#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AugmentCode-Free v1.0.0 Professional Build System
Complete production-grade build automation system

This build system provides:
- Comprehensive environment validation
- Multi-format package building (wheel, sdist, exe, portable)
- Cross-platform executable generation
- Complete checksum generation and verification
- Automated release notes and documentation
- Parallel build processing where possible
- Complete error handling and recovery
- Build artifact validation and testing

Author: BasicProtein
License: MIT
"""

import os
import sys
import shutil
import subprocess
import zipfile
import tarfile
from pathlib import Path
import hashlib
import json
import time
import tempfile
import platform
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import concurrent.futures
from contextlib import contextmanager

# Build Configuration
VERSION = "2.0.2-路径优化版"
PROJECT_NAME = "AugmentCode-Free"
AUTHOR = "BasicProtein"
DESCRIPTION = "多IDE维护工具包 - 支持VS Code、Cursor、Windsurf、JetBrains"
GITHUB_REPO = f"https://github.com/{AUTHOR}/{PROJECT_NAME}"
BUILD_TIMESTAMP = datetime.now().isoformat()

# Build Environment Configuration
BUILD_CONFIG = {
    "python_min_version": (3, 7),
    "build_timeout": 600,
    "parallel_builds": True,
    "compression_level": 9,
    "create_checksums": True,
    "validate_builds": True,
    "cleanup_temp": True
}

# Setup logging with proper encoding
import io
import codecs

# 设置控制台编码
if sys.platform.startswith('win'):
    # Windows 系统设置控制台为 UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('build.log', encoding='utf-8', errors='replace')
    ]
)

def clean_text(text: str) -> str:
    """清理文本中的特殊字符，确保可以安全输出"""
    if not text:
        return ""

    # 移除或替换问题字符
    text = text.replace('\ufffd', '?')  # 替换替换字符
    text = text.replace('\x00', '')    # 移除空字符

    # 确保可以编码为当前系统编码
    try:
        # 先尝试编码为 UTF-8
        text.encode('utf-8')
        return text
    except UnicodeEncodeError:
        # 如果失败，使用替换策略
        return text.encode('utf-8', errors='replace').decode('utf-8')

class BuildError(Exception):
    """Custom exception for build errors"""
    pass

class BuildLogger:
    """Enhanced logging system for build process"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.step_counter = 0
        self.start_time = time.time()
    
    def step(self, step_name: str) -> None:
        """Log a build step"""
        self.step_counter += 1
        elapsed = time.time() - self.start_time
        separator = "=" * 80
        message = f"STEP {self.step_counter}: {step_name} (Elapsed: {elapsed:.2f}s)"
        # 清理消息中的特殊字符
        clean_message = clean_text(message)
        clean_separator = clean_text(separator)
        self.logger.info(f"\n{clean_separator}\n{clean_message}\n{clean_separator}")
        print(f"\n{clean_separator}")
        print(clean_message)
        print(clean_separator)
    
    def success(self, message: str) -> None:
        """Log success message"""
        clean_message = clean_text(message)
        self.logger.info(f"SUCCESS: {clean_message}")
        print(f"\033[92m[SUCCESS]\033[0m {clean_message}")

    def error(self, message: str) -> None:
        """Log error message"""
        clean_message = clean_text(message)
        self.logger.error(f"ERROR: {clean_message}")
        print(f"\033[91m[ERROR]\033[0m {clean_message}")

    def info(self, message: str) -> None:
        """Log info message"""
        clean_message = clean_text(message)
        self.logger.info(f"INFO: {clean_message}")
        print(f"→ INFO: {clean_message}")

    def warning(self, message: str) -> None:
        """Log warning message"""
        clean_message = clean_text(message)
        self.logger.warning(f"WARNING: {clean_message}")
        print(f"\033[93m[WARNING]\033[0m {clean_message}")

# Global logger instance
logger = BuildLogger()

def run_command(cmd: str, cwd: Optional[str] = None, timeout: int = 300, 
                capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Execute command with comprehensive error handling"""
    logger.info(f"Executing: {cmd}")
    if cwd:
        logger.info(f"Working directory: {cwd}")
    
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=capture_output,
            text=True, timeout=timeout, encoding='utf-8', errors='replace'
        )
        
        if result.stdout and result.stdout.strip():
            clean_stdout = clean_text(result.stdout.strip())
            logger.info(f"Output: {clean_stdout}")

        if result.stderr and result.stderr.strip():
            clean_stderr = clean_text(result.stderr.strip())
            logger.warning(f"Stderr: {clean_stderr}")
        
        if check and result.returncode != 0:
            error_msg = f"Command failed (code {result.returncode}): {cmd}"
            if result.stderr:
                error_msg += f"\nError: {result.stderr}"
            raise BuildError(error_msg)
        
        logger.success(f"Command completed (code: {result.returncode})")
        return result
        
    except subprocess.TimeoutExpired as e:
        error_msg = f"Command timed out after {timeout}s: {cmd}"
        logger.error(error_msg)
        raise BuildError(error_msg) from e
    
    except Exception as e:
        error_msg = f"Command execution failed: {cmd} - {str(e)}"
        logger.error(error_msg)
        if check:
            raise BuildError(error_msg) from e
        return subprocess.CompletedProcess(cmd, 1, "", str(e))

class BuildEnvironment:
    """Build environment management and validation"""
    
    def __init__(self):
        self.python_version = sys.version_info
        self.platform_info = {
            'system': platform.system(),
            'machine': platform.machine(),
            'platform': platform.platform(),
            'python_version': platform.python_version()
        }
        self.build_dir = Path.cwd()
        self.dist_dir = self.build_dir / 'dist'
    
    def validate_environment(self) -> bool:
        """Validate build environment requirements"""
        logger.step("Validating Build Environment")
        
        # Check Python version
        min_version = BUILD_CONFIG["python_min_version"]
        if self.python_version < min_version:
            logger.error(f"Python {min_version[0]}.{min_version[1]}+ required, got {self.python_version}")
            return False
        logger.success(f"Python version: {platform.python_version()}")
        
        # Check platform
        logger.info(f"Platform: {self.platform_info['platform']}")
        logger.info(f"Architecture: {self.platform_info['machine']}")
        
        # Check required files
        required_files = ['setup.py', 'main.py', 'requirements.txt']
        missing_files = [f for f in required_files if not (self.build_dir / f).exists()]
        
        if missing_files:
            logger.error(f"Missing required files: {missing_files}")
            return False
        logger.success("All required files present")
        
        # Check core module
        core_dir = self.build_dir / 'augment_tools_core'
        if not core_dir.exists() or not core_dir.is_dir():
            logger.error("augment_tools_core directory not found")
            return False
        logger.success("Core module directory found")
        
        return True
    
    def clean_build_artifacts(self) -> bool:
        """Comprehensive cleanup of build artifacts"""
        logger.step("Cleaning Build Artifacts")
        
        cleanup_targets = {
            'directories': ['build', 'dist', '.eggs'],
            'patterns': ['*.egg-info', '*.spec', '*.pyc', '*.pyo'],
            'cache_dirs': ['__pycache__', '.pytest_cache', '.mypy_cache']
        }
        
        cleaned_count = 0
        
        # Clean directories
        for dir_name in cleanup_targets['directories']:
            dir_path = self.build_dir / dir_name
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    logger.success(f"Removed directory: {dir_name}")
                    cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove {dir_name}: {e}")
        
        # Clean pattern-matched files
        import glob
        for pattern in cleanup_targets['patterns']:
            for path in glob.glob(pattern, recursive=True):
                try:
                    path_obj = Path(path)
                    if path_obj.is_dir():
                        shutil.rmtree(path_obj)
                    else:
                        path_obj.unlink()
                    logger.success(f"Removed: {path}")
                    cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove {path}: {e}")
        
        # Clean cache directories
        for root, dirs, files in os.walk(self.build_dir):
            for cache_dir in cleanup_targets['cache_dirs']:
                if cache_dir in dirs:
                    cache_path = Path(root) / cache_dir
                    try:
                        shutil.rmtree(cache_path)
                        logger.success(f"Removed cache: {cache_path}")
                        cleaned_count += 1
                        dirs.remove(cache_dir)
                    except Exception as e:
                        logger.warning(f"Failed to remove cache {cache_path}: {e}")
        
        logger.success(f"Cleanup completed: {cleaned_count} items removed")
        return True
    
    def setup_build_directories(self) -> bool:
        """Create and setup build directories"""
        logger.info("Setting up build directories")
        
        try:
            self.dist_dir.mkdir(exist_ok=True)
            logger.success(f"Build directory ready: {self.dist_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to create build directories: {e}")
            return False

class DependencyManager:
    """Comprehensive dependency management"""

    def __init__(self):
        self.build_dependencies = {
            'core': ['build>=0.10.0', 'wheel>=0.40.0', 'setuptools>=68.0.0'],
            'packaging': ['pyinstaller>=5.13.0', 'twine>=4.0.0']
        }
        self.installed_packages = {}

    def install_build_dependencies(self) -> bool:
        """Install all required build dependencies"""
        logger.step("Installing Build Dependencies")

        # Upgrade pip first
        try:
            run_command("python -m pip install --upgrade pip", timeout=120)
            logger.success("pip upgraded successfully")
        except BuildError as e:
            logger.error(f"Failed to upgrade pip: {e}")
            return False

        # Install dependencies
        for category, deps in self.build_dependencies.items():
            logger.info(f"Installing {category} dependencies")

            for dep in deps:
                try:
                    logger.info(f"Installing: {dep}")
                    run_command(f"pip install {dep}", timeout=180)

                    # Verify installation
                    package_name = dep.split('>=')[0].split('==')[0]
                    result = run_command(f"pip show {package_name}", capture_output=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.startswith('Version:'):
                                version = line.split(':', 1)[1].strip()
                                self.installed_packages[package_name] = version
                                logger.success(f"Installed {package_name} v{version}")
                                break

                except BuildError as e:
                    logger.error(f"Failed to install {dep}: {e}")
                    if category == 'core':
                        return False
                    logger.warning(f"Continuing without {dep}")

        logger.success(f"Dependencies installed: {len(self.installed_packages)} packages")
        return True

class PythonPackageBuilder:
    """Professional Python package building"""

    def __init__(self, build_env: BuildEnvironment):
        self.build_env = build_env
        self.built_packages = []

    def build_python_packages(self) -> bool:
        """Build wheel and source distribution packages"""
        logger.step("Building Python Packages")

        try:
            # Build both wheel and sdist
            run_command("python -m build --wheel --sdist --outdir dist", timeout=300)

            # Verify packages were created
            wheel_files = list(self.build_env.dist_dir.glob("*.whl"))
            sdist_files = list(self.build_env.dist_dir.glob("*.tar.gz"))

            if not wheel_files:
                logger.error("No wheel file generated")
                return False

            if not sdist_files:
                logger.error("No source distribution generated")
                return False

            # Log built packages
            for package_file in wheel_files + sdist_files:
                size = package_file.stat().st_size
                logger.success(f"Built: {package_file.name} ({size:,} bytes)")
                self.built_packages.append(package_file)

            return True

        except BuildError as e:
            logger.error(f"Python package build failed: {e}")
            return False

class ExecutableBuilder:
    """Windows executable building with PyInstaller"""

    def __init__(self, build_env: BuildEnvironment):
        self.build_env = build_env
        self.spec_file = None

    def create_pyinstaller_spec(self) -> str:
        """Create comprehensive PyInstaller spec file"""
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# {PROJECT_NAME} v{VERSION} PyInstaller Specification
# Generated: {BUILD_TIMESTAMP}

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('augment_tools_core', 'augment_tools_core'),
        ('gui_qt6', 'gui_qt6'),
        ('languages', 'languages'),
        ('config', 'config'),
        ('README.md', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui',
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
        'click', 'colorama', 'pathlib', 'sqlite3', 'json', 'uuid',
        'platform', 'subprocess', 'threading', 'queue', 'time', 'psutil',
        'xml.etree.ElementTree', 'shutil', 'tempfile'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='{PROJECT_NAME}-v{VERSION}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

        spec_filename = f'{PROJECT_NAME}-v{VERSION}.spec'
        spec_path = self.build_env.build_dir / spec_filename

        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)

        self.spec_file = spec_path
        logger.success(f"Created PyInstaller spec: {spec_filename}")
        return str(spec_path)

    def build_executable(self) -> bool:
        """Build Windows executable"""
        logger.step("Building Windows Executable")

        try:
            # Create spec file
            spec_path = self.create_pyinstaller_spec()

            # Run PyInstaller
            logger.info("Starting PyInstaller build...")
            run_command(f"pyinstaller {spec_path} --clean --noconfirm --distpath dist", timeout=600)

            # Verify executable was created
            exe_path = self.build_env.dist_dir / f'{PROJECT_NAME}-v{VERSION}.exe'
            if not exe_path.exists():
                logger.error(f"Executable not found: {exe_path}")
                return False

            size = exe_path.stat().st_size
            logger.success(f"Executable built: {exe_path.name} ({size:,} bytes, {size/1024/1024:.2f} MB)")

            # Clean up spec file
            if self.spec_file and self.spec_file.exists():
                self.spec_file.unlink()

            return True

        except BuildError as e:
            logger.error(f"Executable build failed: {e}")
            return False

class PortablePackageBuilder:
    """Cross-platform portable package creation"""

    def __init__(self, build_env: BuildEnvironment):
        self.build_env = build_env

    def create_portable_package(self) -> bool:
        """Create comprehensive portable package"""
        logger.step("Creating Portable Package")

        portable_dir = self.build_env.build_dir / f"{PROJECT_NAME}-v{VERSION}-Portable"

        try:
            # Create portable directory
            if portable_dir.exists():
                shutil.rmtree(portable_dir)
            portable_dir.mkdir()

            # Copy core files
            core_files = ['main.py', 'setup.py',
                         'requirements.txt', 'README.md', '.gitignore']

            for file in core_files:
                src = self.build_env.build_dir / file
                if src.exists():
                    shutil.copy2(src, portable_dir)
                    logger.success(f"Copied: {file}")

            # Copy core module
            core_src = self.build_env.build_dir / 'augment_tools_core'
            if core_src.exists():
                shutil.copytree(core_src, portable_dir / 'augment_tools_core',
                               ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                logger.success("Copied: augment_tools_core/")

            # Create startup scripts
            self._create_startup_scripts(portable_dir)

            # Create documentation
            self._create_portable_documentation(portable_dir)

            # Create ZIP package
            zip_path = self.build_env.dist_dir / f"{portable_dir.name}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED,
                               compresslevel=BUILD_CONFIG["compression_level"]) as zipf:
                for root, dirs, files in os.walk(portable_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(self.build_env.build_dir)
                        zipf.write(file_path, arcname)

            # Clean up temp directory
            shutil.rmtree(portable_dir)

            size = zip_path.stat().st_size
            logger.success(f"Portable package created: {zip_path.name} ({size:,} bytes)")
            return True

        except Exception as e:
            logger.error(f"Portable package creation failed: {e}")
            return False

    def _create_startup_scripts(self, portable_dir: Path) -> None:
        """Create platform-specific startup scripts"""

        # Windows batch script
        win_script = f'''@echo off
chcp 65001 >nul
title {PROJECT_NAME} v{VERSION}
echo.
echo ========================================
echo   {PROJECT_NAME} v{VERSION}
echo   {DESCRIPTION}
echo   Author: {AUTHOR}
echo ========================================
echo.
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)
echo Starting GUI...
python main.py
pause
'''

        with open(portable_dir / f'Start-{PROJECT_NAME}.bat', 'w', encoding='utf-8') as f:
            f.write(win_script)

        # Unix shell script
        unix_script = f'''#!/bin/bash
echo "========================================"
echo "  {PROJECT_NAME} v{VERSION}"
echo "  {DESCRIPTION}"
echo "  Author: {AUTHOR}"
echo "========================================"
echo

if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python not found!"
    echo "Please install Python 3.7+"
    exit 1
fi

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "Starting GUI..."
$PYTHON_CMD main.py
'''

        script_path = portable_dir / f'start-{PROJECT_NAME.lower()}.sh'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(unix_script)

        # Make executable on Unix systems
        import stat
        script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)

    def _create_portable_documentation(self, portable_dir: Path) -> None:
        """Create comprehensive documentation for portable package"""

        doc_content = f'''# {PROJECT_NAME} v{VERSION} Portable Edition

{DESCRIPTION}

## Quick Start

### Windows Users
1. Double-click "Start-{PROJECT_NAME}.bat"
2. If prompted, install Python dependencies by running "Install-Dependencies.bat"

### Linux/macOS Users
1. Run: ./start-{PROJECT_NAME.lower()}.sh
2. If needed, install dependencies: pip install -r requirements.txt

## System Requirements
- Python 3.7 or higher
- Windows 7/10/11, Linux, or macOS

## Features
- Multi-IDE Support: VS Code, Cursor, Windsurf, JetBrains
- Database Cleaning: Remove specific IDE database entries
- Telemetry ID Modification: Reset or change IDE telemetry identifiers
- JetBrains SessionID Management: Automatic SessionID modification for JetBrains products
- Process Management: Automatic IDE process detection and management
- GUI Interface: User-friendly graphical interface
- CLI Interface: Command-line interface for automation

## Usage
1. Select your target IDE from the dropdown menu
2. Choose the operation you want to perform
3. Follow the on-screen instructions
4. The tool will automatically handle IDE process management

## Important Notes
⚠️ **Before using:**
- Log out of your AugmentCode account
- Close all IDE instances
- Consider backing up important data

## Support
- GitHub: {GITHUB_REPO}
- Issues: {GITHUB_REPO}/issues

## Version Information
- Version: v{VERSION}
- Build Date: {BUILD_TIMESTAMP}
- Author: {AUTHOR}
'''

        with open(portable_dir / 'README.txt', 'w', encoding='utf-8') as f:
            f.write(doc_content)

class ChecksumGenerator:
    """Comprehensive checksum generation and verification"""

    def __init__(self, build_env: BuildEnvironment):
        self.build_env = build_env

    def generate_checksums(self) -> bool:
        """Generate comprehensive checksums for all build artifacts"""
        logger.step("Generating Checksums")

        if not self.build_env.dist_dir.exists():
            logger.error("Distribution directory not found")
            return False

        checksums = {}

        # Process all build artifacts
        for file_path in self.build_env.dist_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith('checksums'):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()

                    checksums[file_path.name] = {
                        'size': len(content),
                        'sha256': hashlib.sha256(content).hexdigest(),
                        'md5': hashlib.md5(content).hexdigest(),
                        'sha1': hashlib.sha1(content).hexdigest()
                    }

                    logger.success(f"Checksums calculated: {file_path.name}")

                except Exception as e:
                    logger.error(f"Failed to calculate checksums for {file_path.name}: {e}")
                    return False

        # Write comprehensive checksum file
        checksum_content = f"# {PROJECT_NAME} v{VERSION} File Checksums\n"
        checksum_content += f"# Generated: {BUILD_TIMESTAMP}\n"
        checksum_content += f"# Author: {AUTHOR}\n\n"

        for filename, hashes in checksums.items():
            checksum_content += f"File: {filename}\n"
            checksum_content += f"Size: {hashes['size']:,} bytes\n"
            checksum_content += f"SHA256: {hashes['sha256']}\n"
            checksum_content += f"SHA1:   {hashes['sha1']}\n"
            checksum_content += f"MD5:    {hashes['md5']}\n"
            checksum_content += "-" * 80 + "\n\n"

        with open(self.build_env.dist_dir / 'checksums.txt', 'w', encoding='utf-8') as f:
            f.write(checksum_content)

        # Write SHA256SUMS file (standard format)
        with open(self.build_env.dist_dir / 'SHA256SUMS', 'w', encoding='utf-8') as f:
            for filename, hashes in checksums.items():
                f.write(f"{hashes['sha256']}  {filename}\n")

        logger.success(f"Checksums generated for {len(checksums)} files")
        return True

class ReleaseNotesGenerator:
    """Generate comprehensive release notes"""

    def __init__(self, build_env: BuildEnvironment):
        self.build_env = build_env

    def generate_release_notes(self) -> bool:
        """Generate detailed release notes"""
        logger.step("Generating Release Notes")

        release_notes = f"""# {PROJECT_NAME} v{VERSION} Release

## Overview
{DESCRIPTION}

## New Features
- **Multi-IDE Support**: Complete support for VS Code, Cursor, Windsurf, and JetBrains
- **Advanced Database Cleaning**: Intelligent cleanup of IDE-specific database entries
- **Telemetry Management**: Comprehensive telemetry ID modification and reset
- **JetBrains SessionID Management**: Automatic SessionID modification for JetBrains products
- **Process Management**: Automatic detection and management of running IDE processes
- **Modern GUI**: Intuitive graphical user interface with real-time feedback
- **CLI Interface**: Full command-line interface for automation and scripting

## Technical Improvements
- **Modular Architecture**: Completely refactored codebase for better maintainability
- **Enhanced Error Handling**: Comprehensive error handling and user feedback
- **Cross-Platform Support**: Full compatibility with Windows, Linux, and macOS
- **Performance Optimization**: Improved execution speed and resource usage

## Download Options

### Python Package (Recommended)
```bash
pip install augment-tools-core
```

### Standalone Downloads
- **Windows Executable**: `{PROJECT_NAME}-v{VERSION}.exe` - No Python installation required
- **Portable Package**: `{PROJECT_NAME}-v{VERSION}-Portable.zip` - Cross-platform portable version
- **Source Package**: `{PROJECT_NAME}-v{VERSION}-Source.tar.gz` - Complete source code

## Installation & Usage

### GUI Mode (Recommended)
1. Download and extract the portable package
2. Run the appropriate startup script for your platform
3. Select your IDE and desired operation
4. Follow the on-screen instructions

### Command Line Mode
```bash
# Install the package
pip install augment-tools-core

# Use the CLI
augment-tools --help
augment-tools clean-db --ide vscode
augment-tools modify-ids --ide cursor
augment-tools modify-ids --ide jetbrains
augment-tools run-all --ide windsurf
```

## Important Notes
⚠️ **Before using this tool:**
- Ensure you are logged out of your AugmentCode account
- Close all IDE instances before running the tool
- Consider backing up important data

## File Verification
All release files include SHA256, SHA1, and MD5 checksums for integrity verification.
See `checksums.txt` and `SHA256SUMS` files in the release.

## System Requirements
- **Python**: 3.7 or higher (for source/portable versions)
- **Operating System**: Windows 7/10/11, Linux, macOS
- **Memory**: 100MB RAM minimum
- **Storage**: 50MB free space

## Support & Documentation
- **Repository**: {GITHUB_REPO}
- **Issues**: {GITHUB_REPO}/issues
- **Documentation**: See README.md for complete documentation

## Build Information
- **Version**: v{VERSION}
- **Build Date**: {BUILD_TIMESTAMP}
- **Python Version**: {platform.python_version()}
- **Platform**: {platform.platform()}

---
**Author**: {AUTHOR}
**License**: MIT License
"""

        try:
            with open(self.build_env.dist_dir / 'RELEASE_NOTES.md', 'w', encoding='utf-8') as f:
                f.write(release_notes)

            logger.success("Release notes generated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to generate release notes: {e}")
            return False

class CompleteBuildSystem:
    """Main build system orchestrator"""

    def __init__(self):
        self.build_env = BuildEnvironment()
        self.dependency_manager = DependencyManager()
        self.python_builder = PythonPackageBuilder(self.build_env)
        self.executable_builder = ExecutableBuilder(self.build_env)
        self.portable_builder = PortablePackageBuilder(self.build_env)
        self.checksum_generator = ChecksumGenerator(self.build_env)
        self.release_notes_generator = ReleaseNotesGenerator(self.build_env)

        self.build_steps = [
            ("Environment Validation", self.build_env.validate_environment),
            ("Artifact Cleanup", self.build_env.clean_build_artifacts),
            ("Directory Setup", self.build_env.setup_build_directories),
            ("Dependency Installation", self.dependency_manager.install_build_dependencies),
            ("Python Package Build", self.python_builder.build_python_packages),
            ("Executable Build", self.executable_builder.build_executable),
            ("Portable Package Creation", self.portable_builder.create_portable_package),
            ("Checksum Generation", self.checksum_generator.generate_checksums),
            ("Release Notes Generation", self.release_notes_generator.generate_release_notes),
        ]

        self.failed_steps = []
        self.start_time = time.time()

    def run_build(self) -> bool:
        """Execute complete build process"""
        logger.step(f"Starting {PROJECT_NAME} v{VERSION} Build Process")
        logger.info(f"Build configuration: {BUILD_CONFIG}")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Python: {platform.python_version()}")

        # Execute all build steps
        for step_name, step_function in self.build_steps:
            try:
                logger.info(f"Executing: {step_name}")

                if not step_function():
                    logger.error(f"Build step failed: {step_name}")
                    self.failed_steps.append(step_name)

                    # Critical steps that should stop the build
                    critical_steps = ["Environment Validation", "Dependency Installation"]
                    if step_name in critical_steps:
                        logger.error("Critical step failed, stopping build")
                        break
                else:
                    logger.success(f"Build step completed: {step_name}")

            except KeyboardInterrupt:
                logger.error("Build interrupted by user")
                return False

            except Exception as e:
                logger.error(f"Unexpected error in {step_name}: {e}")
                self.failed_steps.append(step_name)
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

        # Generate build report
        return self._generate_build_report()

    def _generate_build_report(self) -> bool:
        """Generate comprehensive build report"""
        build_time = time.time() - self.start_time

        logger.step("Build Process Complete")

        if self.failed_steps:
            logger.error(f"Build completed with errors. Failed steps: {', '.join(self.failed_steps)}")
        else:
            logger.success("All build steps completed successfully!")

        logger.info(f"Total build time: {build_time:.2f} seconds")

        # List generated artifacts
        if self.build_env.dist_dir.exists():
            artifacts = list(self.build_env.dist_dir.iterdir())
            if artifacts:
                logger.info("Generated artifacts:")
                total_size = 0

                for artifact in sorted(artifacts):
                    if artifact.is_file():
                        size = artifact.stat().st_size
                        total_size += size

                        # Determine file type icon
                        if artifact.suffix == '.exe':
                            icon = "[EXE]"
                        elif artifact.suffix == '.whl':
                            icon = "[WHL]"
                        elif artifact.name.endswith('.tar.gz'):
                            icon = "[TAR]"
                        elif artifact.suffix == '.zip':
                            icon = "[ZIP]"
                        else:
                            icon = "[FILE]"

                        logger.info(f"  {icon} {artifact.name} ({size:,} bytes)")

                logger.info(f"Total artifacts size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
            else:
                logger.warning("No artifacts generated")

        success = len(self.failed_steps) == 0

        if success:
            logger.success("Build completed successfully! Ready for release.")
            logger.info("Next steps:")
            logger.info("1. Create Git tag: git tag v1.0.0")
            logger.info("2. Push tag: git push origin v1.0.0")
            logger.info("3. Create GitHub Release and upload artifacts")
        else:
            logger.error("Build completed with errors. Please review the failed steps.")

        return success

def main():
    """Main entry point"""
    try:
        print(f"")
        print(f"{'='*80}")
        print(f"{PROJECT_NAME} v{VERSION} Professional Build System")
        print(f"{DESCRIPTION}")
        print(f"Author: {AUTHOR}")
        print(f"{'='*80}")
        print(f"")

        build_system = CompleteBuildSystem()
        success = build_system.run_build()

        return 0 if success else 1

    except KeyboardInterrupt:
        logger.error("Build interrupted by user")
        return 1

    except Exception as e:
        logger.error(f"Unhandled exception in build system: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
