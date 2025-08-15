#!/usr/bin/env python3
"""
Language Manager for AugmentCode-Free
Handles internationalization and language switching functionality.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class LanguageManager:
    """Manages language switching and internationalization"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.current_language = "zh_CN"  # Default language
        self.languages = {}
        self.available_languages = {
            "zh_CN": "简体中文",
            "en_US": "English"
        }
        
        # Load languages
        self._load_languages()
        
        # Set language from config if available
        if config_manager:
            saved_language = config_manager.get_setting("language", "zh_CN")
            self.set_language(saved_language)
    
    def _load_languages(self):
        """Load all available language files"""
        # 处理PyInstaller打包后的资源路径
        if getattr(sys, 'frozen', False):
            # PyInstaller打包后的环境
            base_path = Path(sys._MEIPASS)
        else:
            # 开发环境
            base_path = Path(__file__).resolve().parent

        languages_dir = base_path / "languages"
        
        for lang_code in self.available_languages.keys():
            lang_file = languages_dir / f"{lang_code}.json"
            if lang_file.exists():
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.languages[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading language file {lang_file}: {e}")
                    # Fallback to empty dict
                    self.languages[lang_code] = {}
            else:
                print(f"Language file not found: {lang_file}")
                print(f"Expected path: {lang_file.resolve()}")
                self.languages[lang_code] = {}
    
    def set_language(self, language_code: str):
        """Set current language"""
        if language_code in self.available_languages:
            self.current_language = language_code
            
            # Save to config if available
            if self.config_manager:
                self.config_manager.set_setting("language", language_code)
        else:
            print(f"Unsupported language: {language_code}")
    
    def get_language(self) -> str:
        """Get current language code"""
        return self.current_language
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages dict"""
        return self.available_languages.copy()
    
    def get_text(self, key_path: str, **kwargs) -> str:
        """
        Get translated text by key path
        
        Args:
            key_path: Dot-separated path to the text (e.g., 'buttons.ok')
            **kwargs: Variables for string formatting
            
        Returns:
            Translated text or key_path if not found
        """
        try:
            # Get current language data
            lang_data = self.languages.get(self.current_language, {})
            
            # Navigate through the nested dict using key path
            keys = key_path.split('.')
            value = lang_data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    # Fallback to English if current language doesn't have the key
                    if self.current_language != "en_US":
                        return self._get_fallback_text(key_path, **kwargs)
                    else:
                        # Return key path if even English doesn't have it
                        return key_path
            
            # Format string with provided kwargs
            if isinstance(value, str) and kwargs:
                try:
                    return value.format(**kwargs)
                except KeyError as e:
                    print(f"Missing format key {e} for text: {value}")
                    return value
            
            return str(value)
            
        except Exception as e:
            print(f"Error getting text for key '{key_path}': {e}")
            return key_path
    
    def _get_fallback_text(self, key_path: str, **kwargs) -> str:
        """Get fallback text from English"""
        try:
            lang_data = self.languages.get("en_US", {})
            keys = key_path.split('.')
            value = lang_data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return key_path
            
            if isinstance(value, str) and kwargs:
                try:
                    return value.format(**kwargs)
                except KeyError:
                    return value
            
            return str(value)
            
        except Exception:
            return key_path
    
    def get_language_display_name(self, language_code: str = None) -> str:
        """Get display name for language"""
        if language_code is None:
            language_code = self.current_language
        return self.available_languages.get(language_code, language_code)


# Global language manager instance
_language_manager = None


def get_language_manager(config_manager=None):
    """Get global language manager instance"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager(config_manager)
    return _language_manager


def get_text(key_path: str, **kwargs) -> str:
    """Convenience function to get translated text"""
    return get_language_manager().get_text(key_path, **kwargs)


def set_language(language_code: str):
    """Convenience function to set language"""
    get_language_manager().set_language(language_code)


def get_current_language() -> str:
    """Convenience function to get current language"""
    return get_language_manager().get_language()
