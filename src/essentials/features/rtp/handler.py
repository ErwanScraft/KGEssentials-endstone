import math
import time

from endstone import Player
from endstone.command import (
    Command,
    CommandExecutor,
    CommandSender,
)

from .service import RtpService


class RtpHandler(CommandExecutor):
    def __init__(self, plugin) -> None:
        super().__init__()
        self.plugin = plugin
        self.service = RtpService(plugin)
        self._cooldowns: dict[object, float] = {}

    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: list[str],
    ) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(
                self.plugin.messages.format(
                    "callback.player_only"
                )
            )
            return False

        if command.name != "rtp":
            return False

        return self._rtp(sender)

    def _rtp(
        self,
        player: Player,
    ) -> bool:
        radius = max(
            1.0,
            self._get_number(
                "rtp.radius",
                500.0,
            ),
        )

        attempts = max(
            1,
            int(
                self._get_number(
                    "rtp.attempts",
                    16.0,
                )
            ),
        )

        cooldown = max(
            0.0,
            self._get_number(
                "rtp.cooldown",
                30.0,
            ),
        )

        if not self._check_cooldown(
            player,
            cooldown,
        ):
            return False

        origin = player.location

        target = self.service.find_location(
            origin.dimension,
            origin.x,
            origin.z,
            radius,
            attempts,
        )

        if target is None:
            self.plugin.logger.warning(
                f"RTP failed for {player.name}: "
                f"no safe location found after "
                f"{attempts} attempts."
            )

            self._send(
                player,
                "rtp.failed",
            )

            return False

        try:
            teleported = player.teleport(target)
        except Exception as exc:
            self.plugin.logger.error(
                f"RTP teleport error for "
                f"{player.name}: {exc}"
            )

            self._send(
                player,
                "rtp.failed",
            )

            return False

        if not teleported:
            self.plugin.logger.warning(
                f"RTP teleport rejected for "
                f"{player.name}."
            )

            self._send(
                player,
                "rtp.failed",
            )

            return False

        if cooldown > 0:
            self._cooldowns[player.unique_id] = (
                time.monotonic()
            )

        self._send(
            player,
            "rtp.teleported",
        )

        return True

    def _check_cooldown(
        self,
        player: Player,
        cooldown: float,
    ) -> bool:
        if cooldown <= 0:
            return True

        last_used = self._cooldowns.get(
            player.unique_id
        )

        if last_used is None:
            return True

        remaining = cooldown - (
            time.monotonic() - last_used
        )

        if remaining <= 0:
            return True

        self._send(
            player,
            "rtp.cooldown",
            time=max(
                1,
                math.ceil(remaining),
            ),
        )

        return False

    def _send(
        self,
        player: Player,
        key: str,
        **kwargs,
    ) -> None:
        try:
            message = self.plugin.messages.format(
                key,
                **kwargs,
            )
        except Exception as exc:
            self.plugin.logger.error(
                f"Failed to format message "
                f"'{key}': {exc}"
            )
            return

        if message:
            player.send_message(message)

    def _get_number(
        self,
        path: str,
        default: float,
    ) -> float:
        value = self.plugin.config_manager.get(
            path,
            default,
        )

        try:
            return float(value)
        except (TypeError, ValueError):
            self.plugin.logger.warning(
                f"Invalid configuration "
                f"'{path}': {value!r}. "
                f"Using default {default}."
            )
            return default