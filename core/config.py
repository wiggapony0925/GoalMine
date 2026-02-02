import json
import os
import re

class Settings:
    """
    Centralized Settings Manager.
    Loads settings.json from root and provides easy access.
    """
    _instance = None
    _settings = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance.load()
        return cls._instance

    def load(self):
        """Loads settings from settings.json in the project root."""
        from core.log import get_logger
        logger = get_logger("Config")
        
        # Go up from GoalMine/core/config.py to GoalMine/
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root_dir, 'settings.json')
        
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    raw_content = f.read()
                    # Strip // comments before parsing JSON
                    clean_content = re.sub(r'//.*', '', raw_content)
                    self._settings = json.loads(clean_content)
                logger.info("⚙️ Settings loaded from settings.json")
            else:
                logger.warning(f"⚠️ settings.json not found at {path}. Using internal defaults.")
                self._settings = {}
        except Exception as e:
            logger.error(f"❌ Error loading settings.json: {e}")
            self._settings = {}

    def get(self, key_path, default=None):
        """
        Retrieves a nested setting using dot notation.
        Example: settings.get('agents.logistics')
        """
        keys = key_path.split('.')
        val = self._settings
        try:
            for k in keys:
                val = val[k]
            return val
        except (KeyError, TypeError):
            return default

# Global instance
settings = Settings()
