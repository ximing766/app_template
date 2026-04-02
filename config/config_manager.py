# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

class ConfigManager:
    """Manages application configuration settings"""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager

        Args:
            config_dir: Custom configuration directory path
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            app_dir = Path(__file__).parent.parent
            self.config_dir = app_dir / "config"

        self.config_dir.mkdir(exist_ok=True)
        self.config_path = self.config_dir / "config.json"
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from single config.json file"""
        default_config = {
            "app": {
                "name": "Generic App",
                "version": "1.0.0",
                "window": {
                    "width": 1200,
                    "height": 800,
                    "min_width": 1000,
                    "min_height": 700
                },
                "features": {
                    "mouse_navigation": True,
                    "background_enabled": True,
                    "theme_switching": True
                },
                "settings": {
                    "language": "english"
                }
            },
            "background": {
                "enabled": True,
                "opacity": 1.0,
                "current_image": "backgrounds/default1.jpg",
                "available_images": [
                    "backgrounds/default1.jpg",
                    "backgrounds/default2.jpg",
                    "backgrounds/default3.jpg"
                ],
                "current_index": 0
            },
            "theme": {
                "current_theme": "dark",
                "themes": {
                    "light": {
                        "name": "Light",
                        "is_dark": False,
                        "primary_color": "#0078d4",
                        "background_color": "#ffffff"
                    },
                    "dark": {
                        "name": "Dark",
                        "is_dark": True,
                        "primary_color": "#0078d4",
                        "background_color": "#202020"
                    }
                }
            },
            "font": {
                "family": "Courier New",
                "size": 10
            }
        }

        return self._load_json_config(self.config_path, default_config)

    def _load_json_config(self, config_path: Path, default_config: Dict[str, Any]) -> Dict[str, Any]:
        """Load JSON configuration with fallback to defaults"""
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                return self._merge_configs(default_config, user_config)
            else:
                self._save_json_config(config_path, default_config)
                return default_config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config from {config_path}: {e}")
            return default_config

    def _save_json_config(self, config_path: Path, config_data: Dict[str, Any]):
        """Save configuration to JSON file"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving config to {config_path}: {e}")

    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with default config"""
        result = default.copy()

        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def get_main_config(self) -> Dict[str, Any]:
        """Get main configuration"""
        return self._config.get("app", {}).copy()

    def get_language(self) -> str:
        """Get current language setting"""
        return self._config.get("app", {}).get("settings", {}).get("language", "english")

    def set_language(self, language: str):
        """Set language setting"""
        if "app" not in self._config:
            self._config["app"] = {}
        if "settings" not in self._config["app"]:
            self._config["app"]["settings"] = {}
        self._config["app"]["settings"]["language"] = language
        self._save_json_config(self.config_path, self._config)

    def update_main_config(self, updates: Dict[str, Any]):
        """Update main configuration"""
        if "app" not in self._config:
            self._config["app"] = {}
        self._config["app"] = self._merge_configs(self._config["app"], updates)
        self._save_json_config(self.config_path, self._config)

    def get_theme(self) -> str:
        """Get current theme name"""
        return self._config.get("theme", {}).get("current_theme", "dark")

    def set_theme(self, theme_name: str):
        """Set current theme"""
        if "theme" not in self._config:
            self._config["theme"] = {}
        self._config["theme"]["current_theme"] = theme_name
        self._save_json_config(self.config_path, self._config)

    def get_font_family(self) -> str:
        """Get current font family"""
        return self._config.get("font", {}).get("family", "Courier New")

    def set_font_family(self, font_family: str):
        """Set font family"""
        if "font" not in self._config:
            self._config["font"] = {}
        self._config["font"]["family"] = font_family
        self._save_json_config(self.config_path, self._config)
        return True

    def get_font_size(self) -> int:
        """Get current font size"""
        return self._config.get("font", {}).get("size", 10)

    def set_font_size(self, font_size: int):
        """Set font size"""
        if "font" not in self._config:
            self._config["font"] = {}
        self._config["font"]["size"] = max(6, min(32, font_size))
        self._save_json_config(self.config_path, self._config)

    def get_background_config(self) -> Dict[str, Any]:
        """Get background configuration"""
        return self._config.get("background", {}).copy()

    def get_background_enabled(self) -> bool:
        """Get background enabled status"""
        return self._config.get("background", {}).get("enabled", False)

    def set_background_enabled(self, enabled: bool):
        """Enable or disable background"""
        if "background" not in self._config:
            self._config["background"] = {}
        self._config["background"]["enabled"] = enabled
        self._save_json_config(self.config_path, self._config)

    def set_background_opacity(self, opacity: float):
        """Set background opacity (0.0 to 1.0)"""
        if "background" not in self._config:
            self._config["background"] = {}
        self._config["background"]["opacity"] = max(0.0, min(1.0, opacity))
        self._save_json_config(self.config_path, self._config)

    def get_background_opacity(self) -> float:
        """Get background opacity"""
        return self._config.get("background", {}).get("opacity", 1.0)

    def get_current_background(self) -> Optional[str]:
        """Get current background image path"""
        return self._config.get("background", {}).get("current_image")

    def get_available_backgrounds(self) -> List[str]:
        """Get list of available background images from assets/PIC folder"""
        assets_pic_dir = Path(__file__).parent.parent / "assets" / "PIC"

        available_images = []
        if assets_pic_dir.exists():
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}

            for file_path in assets_pic_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    relative_path = f"assets/PIC/{file_path.name}"
                    available_images.append(relative_path)

            available_images.sort()

            if "background" not in self._config:
                self._config["background"] = {}
            self._config["background"]["available_images"] = available_images

            current_image = self._config["background"].get("current_image")
            if not current_image or current_image not in available_images:
                if available_images:
                    self._config["background"]["current_image"] = available_images[0]
                    self._config["background"]["current_index"] = 0
            else:
                try:
                    self._config["background"]["current_index"] = available_images.index(current_image)
                except ValueError:
                    self._config["background"]["current_index"] = 0

            self._save_json_config(self.config_path, self._config)

        return available_images

    def set_current_background(self, image_path: str):
        """Set current background image"""
        if "background" not in self._config:
            self._config["background"] = {}

        self._config["background"]["current_image"] = image_path

        available_images = self._config["background"].get("available_images", [])
        if image_path not in available_images:
            available_images.append(image_path)
            self._config["background"]["available_images"] = available_images

        if image_path in available_images:
            self._config["background"]["current_index"] = available_images.index(image_path)

        self._save_json_config(self.config_path, self._config)
        return True

    def save_config(self):
        """Save all configurations to main config file"""
        self._save_json_config(self.config_path, self._config)

    def reload_config(self):
        """Reload all configurations from files"""
        self._config = self._load_config()

    def reset_to_defaults(self):
        """Reset all configurations to defaults"""
        if self.config_path.exists():
            self.config_path.unlink()
        self.reload_config()