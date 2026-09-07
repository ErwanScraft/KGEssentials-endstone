import yaml


class KGEssentialsConfig:
    def __init__(self, plugin) -> None:
        self.path = plugin.data_folder / "config.yml"
        self.data: dict = {}

    def load(self) -> None:
        with self.path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file) or {}

        if not isinstance(config, dict):
            raise ValueError(
                "config.yml must contain a YAML mapping."
            )

        self.data = config

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def get_feature(self, name: str) -> dict:
        feature = self.data.get(name)

        if not isinstance(feature, dict):
            raise ValueError(
                f"'{name}' must be a YAML mapping."
            )

        return feature

    def update_feature(
        self,
        name: str,
        values: dict,
    ) -> None:
        self.get_feature(name)

        self._update_yaml_values(name, values)

        self.data[name].update(values)

    def _update_yaml_values(
        self,
        feature_name: str,
        values: dict,
    ) -> None:
        lines = self.path.read_text(
            encoding="utf-8"
        ).splitlines()

        feature_index = None

        for index, line in enumerate(lines):
            if line.strip() == f"{feature_name}:":
                feature_index = index
                break

        if feature_index is None:
            raise ValueError(
                f"Feature '{feature_name}' was not found "
                "in config.yml."
            )

        feature_end = len(lines)

        for index in range(
            feature_index + 1,
            len(lines),
        ):
            line = lines[index]

            if (
                line
                and not line.startswith(
                    (" ", "\t", "#")
                )
            ):
                feature_end = index
                break

        for key, value in values.items():
            key_index = None

            for index in range(
                feature_index + 1,
                feature_end,
            ):
                if lines[index].startswith(
                    f"  {key}:"
                ):
                    key_index = index
                    break

            formatted_value = self._format_yaml_value(
                value
            )

            if key_index is not None:
                lines[key_index] = (
                    f"  {key}: {formatted_value}"
                )
                continue

            lines.insert(
                feature_end,
                f"  {key}: {formatted_value}",
            )

            feature_end += 1

        self.path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _format_yaml_value(value) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, (int, float)):
            return str(value)

        return yaml.safe_dump(
            value,
            default_flow_style=True,
            allow_unicode=True,
        ).strip()