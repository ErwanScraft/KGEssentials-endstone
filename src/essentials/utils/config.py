from pathlib import Path

import yaml


class KGEssentialsConfig:
    def __init__(self, plugin) -> None:
        self.plugin = plugin
        self.data: dict = {}

    def load(self) -> None:
        path = Path(self.plugin.data_folder) / "config.yml"

        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        if not isinstance(data, dict):
            raise ValueError("config.yml must contain a YAML mapping.")

        self.data = data

    def get(self, key: str, default=None):
        return self.data.get(key, default)