import time

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
        self._cooldowns: dict[object, float] = {}

    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: list[str],
    ) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(
                self.plugin.messages.format("callback.player_only")
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

        self.plugin.spawn_data.update_values(
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
        dimension_name = self.plugin.spawn_data.get(
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
                    self.plugin.spawn_data.get("x")
                ),
                float(
                    self.plugin.spawn_data.get("y")
                ),
                float(
                    self.plugin.spawn_data.get("z")
                ),
                float(
                    self.plugin.spawn_data.get(
                        "pitch",
                        0.0,
                    )
                ),
                float(
                    self.plugin.spawn_data.get(
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

        cooldown = self.plugin.config_manager.get(
            "spawn.cooldown",
            10,
        )

        try:
            cooldown = float(cooldown)
        except (TypeError, ValueError):
            cooldown = 10.0

        cooldown = max(0.0, cooldown)

        player_id = player.unique_id
        now = time.monotonic()
        last_used = self._cooldowns.get(player_id)

        if last_used is not None:
            remaining = cooldown - (now - last_used)

            if remaining > 0:
                player.send_message(
                    self.plugin.messages.format(
                        "spawn.cooldown",
                        time=max(1, round(remaining)),
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

        if cooldown > 0:
            self._cooldowns[player_id] = time.monotonic()

        player.send_message(
            self.plugin.messages.format(
                "spawn.teleported"
            )
        )

        return True