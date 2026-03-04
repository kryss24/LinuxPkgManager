import os
import json
from pathlib import Path

class ConfigManager:
    DEFAULT_CONFIG = {
        "theme": "dark",
        "view_mode": "list",
        "sort_by": "Name A-Z"
    }

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "linuxpkgmanager"
        self.config_file = self.config_dir / "config.json"
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self.config.update(json.load(f))
            except: pass
        else:
            self.save()

    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key):
        return self.config.get(key, self.DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()

config = ConfigManager()
