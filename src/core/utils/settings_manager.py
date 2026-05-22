import json
import os
from typing import Dict, Any

class SettingsManager:
    _instance = None
    _settings: Dict[str, Any] = {
        "appearance": {
            "theme": "dark"  # Default theme
        },
        "language": {
            "current": "en-US"  # Default language
        },
        "features": {
            "advanced_explorer": True  # Enable Advanced Explorer by default
        },
        "debug": {
            "enabled": False,
            "save_logs": False,
            "show_timing": False,
            "show_api": False
        }
    }
    _settings_file = os.path.join("config", "user_settings.json")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_settings()
        return cls._instance
    
    def _load_settings(self):
        """Load settings from file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self._settings_file), exist_ok=True)
            
            if os.path.exists(self._settings_file):
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    # Update settings keeping default values for missing keys
                    self._update_nested_dict(self._settings, saved_settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self._settings_file), exist_ok=True)
            
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def _update_nested_dict(self, d1: dict, d2: dict):
        """Update a nested dictionary maintaining original structure"""
        for k, v in d2.items():
            if k in d1:
                if isinstance(v, dict) and isinstance(d1[k], dict):
                    self._update_nested_dict(d1[k], v)
                else:
                    d1[k] = v
    
    def get_setting(self, *keys: str) -> Any:
        """
        Get a setting using a key path
        Example: get_setting("appearance", "theme")
        """
        value = self._settings
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value
    
    def set_setting(self, *keys_and_value) -> bool:
        """
        Set a setting using a key path and value
        Example: set_setting("appearance", "theme", "dark")
        """
        if len(keys_and_value) < 2:
            return False
            
        *keys, value = keys_and_value
        current = self._settings
        
        # Navigate through dictionary
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
            
        # Set value
        current[keys[-1]] = value
        self._save_settings()
        return True
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Returns all settings"""
        return self._settings.copy()