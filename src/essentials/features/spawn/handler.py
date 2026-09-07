from endstone import Player
from endstone.command import (
    Command,
    CommandExecutor,
    CommandSender,
)
from endstone.level import Location


class SpawnHandler(CommandExecutor):
    def __init__(self, plugin) -> None:
        super().__init__()
        self.plugin = plugin

    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: list[str],
    ) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(
                self.plugin.messages.format(
                    "spawn.player_only"
                )
            )
            return False

        if command.name == "setspawn":
            return self._set_spawn(sender)

        if command.name == "spawn":
            return self._spawn(sender)

        return False

    def _set_spawn(
        self,
        player: Player,
    ) -> bool:
        location = player.location

        self.plugin.spawn_config.update_values(
            {
                "dimension": location.dimension.name,
                "x": location.x,
                "y": location.y,
                "z": location.z,
                "pitch": location.pitch,
                "yaw": location.yaw,
            }
        )

        player.send_message(
            self.plugin.messages.format(
                "spawn.set"
            )
        )

        return True

    def _spawn(
        self,
        player: Player,
    ) -> bool:
        dimension_name = self.plugin.spawn_config.get(
            "dimension"
        )

        if (
            not isinstance(
                dimension_name,
                str,
            )
            or not dimension_name
        ):
            player.send_message(
                self.plugin.messages.format(
                    "spawn.unavailable"
                )
            )
            return False

        try:
            dimension = player.level.get_dimension(
                dimension_name
            )

            location = Location(
                dimension,
                float(
                    self.plugin.spawn_config.get("x")
                ),
                float(
                    self.plugin.spawn_config.get("y")
                ),
                float(
                    self.plugin.spawn_config.get("z")
                ),
                float(
                    self.plugin.spawn_config.get(
                        "pitch",
                        0.0,
                    )
                ),
                float(
                    self.plugin.spawn_config.get(
                        "yaw",
                        0.0,
                    )
                ),
            )
        except (
            TypeError,
            ValueError,
        ):
            player.send_message(
                self.plugin.messages.format(
                    "spawn.unavailable"
                )
            )
            return False

        if not player.teleport(location):
            player.send_message(
                self.plugin.messages.format(
                    "spawn.unavailable"
                )
            )
            return False

        player.send_message(
            self.plugin.messages.format(
                "spawn.teleported"
            )
        )

        return True