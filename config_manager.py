#!/usr/bin/env python3
"""
Configuration Manager for AugmentCode-Free
Handles user settings and configuration persistence.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages user configuration and settings"""
    
    def __init__(self):
        # 处理PyInstaller打包后的资源路径
        if getattr(sys, 'frozen', False):
            # PyInstaller打包后的环境
            base_path = Path(sys._MEIPASS)
        else:
            # 开发环境
            base_path = Path(__file__).resolve().parent

        self.config_dir = base_path / "config"
        self.config_file = self.config_dir / "settings.json"
        self.settings = {}
        
        # Default settings
        self.default_settings = {
            "language": "zh_CN",
            "first_run": True,
            "window_geometry": "600x780",  # 增加宽度从520到600
            "last_selected_ide": "VS Code",
            "show_welcome": True,
            "show_about_on_startup": True,
            "theme": "default"
        }
        
        # Ensure config directory exists
        self._ensure_config_dir()
        
        # Load existing settings
        self._load_settings()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        try:
            self.config_dir.mkdir(exist_ok=True, parents=True)
            # 在macOS上确保目录权限正确
            if os.name == 'posix':
                os.chmod(self.config_dir, 0o755)
        except Exception as e:
            print(f"Error creating config directory: {e}")
            print(f"Config directory path: {self.config_dir}")
    
    def _load_settings(self):
        """Load settings from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self.settings = {**self.default_settings, **loaded_settings}
            else:
                # Use defaults for first run
                self.settings = self.default_settings.copy()
                self._save_settings()
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = self.default_settings.copy()
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value
        self._save_settings()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.settings.copy()
    
    def reset_settings(self):
        """Reset all settings to defaults"""
        self.settings = self.default_settings.copy()
        self._save_settings()
    
    def is_first_run(self) -> bool:
        """Check if this is the first run"""
        return self.get_setting("first_run", True)
    
    def mark_first_run_complete(self):
        """Mark first run as complete"""
        self.set_setting("first_run", False)
    
    def should_show_welcome(self) -> bool:
        """Check if welcome dialog should be shown"""
        return self.get_setting("show_welcome", True)

    def set_show_welcome(self, show: bool):
        """Set whether to show welcome dialog"""
        self.set_setting("show_welcome", show)

    def should_show_about_on_startup(self) -> bool:
        """Check if about dialog should be shown on startup"""
        return self.get_setting("show_about_on_startup", True)

    def set_show_about_on_startup(self, show: bool):
        """Set whether to show about dialog on startup"""
        self.set_setting("show_about_on_startup", show)
    
    def get_window_geometry(self) -> str:
        """Get window geometry"""
        return self.get_setting("window_geometry", "420x680")
    
    def set_window_geometry(self, geometry: str):
        """Set window geometry"""
        self.set_setting("window_geometry", geometry)
    
    def get_last_selected_ide(self) -> str:
        """Get last selected IDE"""
        return self.get_setting("last_selected_ide", "VS Code")
    
    def set_last_selected_ide(self, ide: str):
        """Set last selected IDE"""
        self.set_setting("last_selected_ide", ide)
    
    def get_language(self) -> str:
        """Get current language"""
        return self.get_setting("language", "zh_CN")
    
    def set_language(self, language: str):
        """Set current language"""
        self.set_setting("language", language)


# Global config manager instance
_config_manager = None


def get_config_manager():
    """Get global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
