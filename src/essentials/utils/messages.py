from pathlib import Path

import yaml


class KGEssentialsMessages:
    def __init__(self, plugin) -> None:
        self.plugin = plugin
        self.data: dict = {}

    def load(self) -> None:
        path = Path(self.plugin.data_folder) / "message.yml"

        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        if not isinstance(data, dict):
            raise ValueError("message.yml must contain a YAML mapping.")

        self.data = data

    def get(self, key: str, default: str = "") -> str:
        value = self.data

        for part in key.split("."):
            if not isinstance(value, dict):
                return default

            value = value.get(part)

            if value is None:
                return default

        if not isinstance(value, str):
            return default

        return value

    def format(self, key: str, **kwargs) -> str:
        message = self.get(key)

        if not message:
            return ""

        values = {
            "prefix": self.plugin._config_manager.get(
                "prefix",
                "KGEssentials",
            ),
            **kwargs,
        }

        return message.format(**values)