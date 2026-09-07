import yaml


class ConfigManager:
    def __init__(
        self,
        plugin,
        filename: str = "config.yml",
    ) -> None:
        self.path = plugin.data_folder / filename
        self.data: dict = {}

    def load(self) -> None:
        with self.path.open(
            "r",
            encoding="utf-8",
        ) as file:
            config = yaml.safe_load(file) or {}

        if not isinstance(config, dict):
            raise ValueError(
                f"{self.path.name} must contain a YAML mapping."
            )

        self.data = config

    def get(
        self,
        key: str,
        default=None,
    ):
        value = self.data

        for part in key.split("."):
            if not isinstance(value, dict):
                return default

            if part not in value:
                return default

            value = value[part]

        return value

    def update(
        self,
        section: str,
        values: dict,
    ) -> None:
        current = self.get(section)

        if not isinstance(current, dict):
            raise ValueError(
                f"'{section}' must be a YAML mapping."
            )

        self._update_yaml_section(
            section,
            values,
        )

        current.update(values)

    def update_values(
        self,
        values: dict,
    ) -> None:
        if not isinstance(values, dict):
            raise ValueError(
                "values must be a dictionary."
            )

        self._update_yaml_root(values)

        self.data.update(values)

    def _update_yaml_section(
        self,
        section: str,
        values: dict,
    ) -> None:
        lines = self.path.read_text(
            encoding="utf-8"
        ).splitlines()

        section_index = None

        for index, line in enumerate(lines):
            if line.strip() == f"{section}:":
                section_index = index
                break

        if section_index is None:
            raise ValueError(
                f"Section '{section}' was not found "
                f"in {self.path.name}."
            )

        section_end = len(lines)

        for index in range(
            section_index + 1,
            len(lines),
        ):
            line = lines[index]

            if (
                line
                and not line.startswith(
                    (" ", "\t", "#")
                )
            ):
                section_end = index
                break

        for key, value in values.items():
            key_index = None

            for index in range(
                section_index + 1,
                section_end,
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
                section_end,
                f"  {key}: {formatted_value}",
            )

            section_end += 1

        self._write_lines(lines)

    def _update_yaml_root(
        self,
        values: dict,
    ) -> None:
        lines = self.path.read_text(
            encoding="utf-8"
        ).splitlines()

        for key, value in values.items():
            key_index = None

            for index, line in enumerate(lines):
                if line.startswith(
                    f"{key}:"
                ):
                    key_index = index
                    break

            formatted_value = self._format_yaml_value(
                value
            )

            if key_index is not None:
                lines[key_index] = (
                    f"{key}: {formatted_value}"
                )
                continue

            insert_index = len(lines)

            for index, line in enumerate(lines):
                if (
                    line
                    and not line.startswith(
                        (" ", "\t", "#")
                    )
                ):
                    insert_index = index

            lines.insert(
                insert_index,
                f"{key}: {formatted_value}",
            )

        self._write_lines(lines)

    def _write_lines(
        self,
        lines: list[str],
    ) -> None:
        self.path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _format_yaml_value(
        value,
    ) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, (int, float)):
            return str(value)

        return yaml.safe_dump(
            value,
            default_flow_style=True,
            allow_unicode=True,
        ).strip()