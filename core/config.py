"""
Configuration Manager for Whisper-Ctrl.

Handles loading, saving, and validating application settings.
Settings are stored in a JSON file in the user's home directory.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages application configuration with JSON persistence."""

    DEFAULT_CONFIG = {
        "backend": "local",  # "local" or "api"
        "local": {
            "model_size": "large-v3",
            "compute_type": "float16",
            "device": "cuda"  # "cuda" or "cpu"
        },
        "api": {
            "type": "openai",       # "openai" or "azure"
            "api_key": "",
            "api_url": "",          # empty = provider default URL
            "model": "whisper-1",   # model name (openai) or deployment name (azure)
            "api_version": "2024-10-21"  # azure only
        },
        "hotkey": {
            "type": "double_ctrl",  # "double_ctrl", "double_alt", "custom"
            "keys": ["ctrl_l", "ctrl_r"],  # Keys to listen for
            "threshold": 0.4  # Double-press threshold in seconds
        },
        "audio": {
            "sample_rate": 16000,
            "language": "pl",  # "en", "pl", "auto", etc.
            "vad_enabled": True,
            "vad_parameters": {
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
                "min_silence_duration_ms": 700
            }
        },
        "ui": {
            "show_notifications": True,
            "feedback_widget_offset_x": 2,
            "feedback_widget_offset_y": 2
        },
        "first_run": True  # Flag for first run wizard
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ConfigManager.

        Args:
            config_path: Optional custom path to config file.
                        If None, uses ~/.config/whisper-ctrl/config.json
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            config_dir = Path.home() / ".config" / "whisper-ctrl"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / "config.json"

        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from JSON file. Creates default if not exists."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._config = self._merge_with_defaults(loaded_config)
                print(f"✅ Configuration loaded from {self.config_path}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Error loading config: {e}. Using defaults.")
                self._config = self.DEFAULT_CONFIG.copy()
                self._save()
        else:
            print(f"📝 No config found. Creating default at {self.config_path}")
            self._config = self.DEFAULT_CONFIG.copy()
            self._save()

    def _migrate_config(self, loaded: Dict) -> Dict:
        """Migrate old config formats to current structure."""
        # Migrate old "openai" section to new "api" section
        if "openai" in loaded and "api" not in loaded:
            loaded["api"] = {
                "type": "openai",
                "api_key": loaded["openai"].get("api_key", ""),
                "api_url": "",
                "model": loaded["openai"].get("model", "whisper-1"),
                "api_version": "2024-10-21"
            }
            if loaded.get("backend") == "openai":
                loaded["backend"] = "api"
            del loaded["openai"]
            print("🔄 Migrated old 'openai' config to new 'api' format")
        return loaded

    def _merge_with_defaults(self, loaded: Dict) -> Dict:
        """Merge loaded config with defaults to handle new keys."""
        loaded = self._migrate_config(loaded)
        merged = self.DEFAULT_CONFIG.copy()

        def deep_update(base: Dict, updates: Dict) -> Dict:
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    base[key] = deep_update(base[key].copy(), value)
                else:
                    base[key] = value
            return base

        return deep_update(merged, loaded)

    def _save(self) -> None:
        """Save current configuration to JSON file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            print(f"💾 Configuration saved to {self.config_path}")
        except IOError as e:
            print(f"❌ Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Examples:
            config.get("backend")  # Returns "local" or "openai"
            config.get("local.model_size")  # Returns "large-v3"
            config.get("hotkey.threshold")  # Returns 0.4

        Args:
            key: Configuration key (supports dot notation for nested values)
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any, save: bool = True) -> None:
        """
        Set a configuration value using dot notation.

        Examples:
            config.set("backend", "openai")
            config.set("openai.api_key", "sk-...")
            config.set("hotkey.threshold", 0.5)

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            save: Whether to save to disk immediately (default: True)
        """
        keys = key.split('.')
        target = self._config

        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # Set the value
        target[keys[-1]] = value

        if save:
            self._save()

    def get_backend_config(self) -> Dict[str, Any]:
        """Get configuration for the currently active backend."""
        backend = self.get("backend", "local")
        return self.get(backend, {})

    def is_first_run(self) -> bool:
        """Check if this is the first run of the application."""
        return self.get("first_run", True)

    def mark_first_run_complete(self) -> None:
        """Mark the first run wizard as completed."""
        self.set("first_run", False)

    def validate_api_config(self) -> bool:
        """
        Validate external API configuration.

        Returns:
            True if API key is set and API type is valid
        """
        api_key = self.get("api.api_key", "")
        api_type = self.get("api.type", "openai")
        if not api_key:
            return False
        if api_type == "azure" and not self.get("api.api_url", ""):
            return False
        return True

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = self.DEFAULT_CONFIG.copy()
        self._save()
        print("🔄 Configuration reset to defaults")

    def export_config(self) -> Dict[str, Any]:
        """Export current configuration as a dictionary."""
        return self._config.copy()

    def import_config(self, config_dict: Dict[str, Any]) -> None:
        """
        Import configuration from a dictionary.

        Args:
            config_dict: Configuration dictionary to import
        """
        self._config = self._merge_with_defaults(config_dict)
        self._save()
