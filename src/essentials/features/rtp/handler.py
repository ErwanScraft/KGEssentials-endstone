import time

from endstone.command import Command, CommandExecutor, CommandSender
from endstone.event import PlayerMoveEvent, event_handler
from endstone.plugin import Plugin

from .service import RtpService


class RtpHandler(CommandExecutor):
    def __init__(self, plugin: Plugin) -> None:
        super().__init__()

        self.plugin = plugin
        self.service = RtpService(plugin)

        self.cooldowns: dict[str, float] = {}
        self.warmups: dict[str, object] = {}

    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: list[str],
    ) -> bool:
        if not hasattr(sender, "location"):
            sender.send_message(
                self.plugin.messages.get(
                    "rtp.player-only"
                )
            )
            return True

        player = sender
        player_id = str(player.unique_id)

        if player_id in self.warmups:
            return True

        remaining = self._get_cooldown_remaining(
            player_id
        )

        if remaining > 0:
            self._send(
                player,
                "rtp.cooldown",
                time=self._format_time(remaining),
            )
            return True

        self._start_warmup(player)

        return True

    def _start_warmup(self, player) -> None:
        player_id = str(player.unique_id)

        warmup_seconds = max(
            0,
            self._get_number(
                "rtp.warmup",
                5,
            ),
        )

        if warmup_seconds <= 0:
            self._execute_rtp(player)
            return

        start_location = player.location

        self._send(
            player,
            "rtp.warmup",
            time=warmup_seconds,
        )

        state = {
            "location": start_location,
            "remaining": warmup_seconds,
            "task": None,
        }

        self.warmups[player_id] = state

        task = self.plugin.server.scheduler.run_task(
            self.plugin,
            lambda: self._warmup_tick(
                player_id
            ),
            delay=0,
            period=20,
        )

        state["task"] = task

    def _warmup_tick(self, player_id: str) -> None:
        state = self.warmups.get(player_id)

        if state is None:
            return

        player = self.plugin.server.get_player(
            player_id
        )

        if player is None:
            self._cancel_warmup(
                player_id
            )
            return

        if not self._is_same_position(
            player.location,
            state["location"],
        ):
            self._cancel_warmup(
                player_id,
                send_message=True,
            )
            return

        state["remaining"] -= 1

        if state["remaining"] <= 0:
            self._finish_warmup(player_id)
            return

        self._send(
            player,
            "rtp.warmup",
            time=state["remaining"],
        )

    def _finish_warmup(self, player_id: str) -> None:
        state = self.warmups.pop(
            player_id,
            None,
        )

        if state is None:
            return

        task = state.get("task")

        if task is not None:
            task.cancel()

        player = self.plugin.server.get_player(
            player_id
        )

        if player is None:
            return

        self._execute_rtp(player)

    def _cancel_warmup(
        self,
        player_id: str,
        send_message: bool = False,
    ) -> None:
        state = self.warmups.pop(
            player_id,
            None,
        )

        if state is None:
            return

        task = state.get("task")

        if task is not None:
            task.cancel()

        if send_message:
            player = self.plugin.server.get_player(
                player_id
            )

            if player is not None:
                self._send(
                    player,
                    "rtp.cancelled",
                )

    def _execute_rtp(self, player) -> None:
        player_id = str(player.unique_id)

        location = player.location
        dimension = location.dimension

        radius = self._get_number(
            "rtp.radius",
            500,
        )

        attempts = self._get_number(
            "rtp.attempts",
            32,
        )

        blacklist_biomes = self._get_blacklist_biomes()

        target = self.service.find_location(
            dimension,
            location.x,
            location.z,
            radius,
            attempts,
            blacklist_biomes,
        )

        if target is None:
            self._send(
                player,
                "rtp.failed",
            )
            return

        try:
            if not player.teleport(target):
                self._send(
                    player,
                    "rtp.failed",
                )
                return
        except Exception as exc:
            self.plugin.logger.debug(
                f"RTP teleport failed for "
                f"{player.name}: {exc}"
            )

            self._send(
                player,
                "rtp.failed",
            )
            return

        cooldown = self._get_number(
            "rtp.cooldown",
            30,
        )

        if cooldown > 0:
            self.cooldowns[player_id] = (
                time.monotonic() + cooldown
            )

        self._send(
            player,
            "rtp.teleported",
        )

    @event_handler
    def on_player_move(
        self,
        event: PlayerMoveEvent,
    ) -> None:
        player = event.player
        player_id = str(player.unique_id)

        if player_id not in self.warmups:
            return

        state = self.warmups[player_id]

        if not self._is_same_position(
            event.to_location,
            state["location"],
        ):
            self._cancel_warmup(
                player_id,
                send_message=True,
            )

    def _get_cooldown_remaining(
        self,
        player_id: str,
    ) -> int:
        expires_at = self.cooldowns.get(
            player_id
        )

        if expires_at is None:
            return 0

        remaining = expires_at - time.monotonic()

        if remaining <= 0:
            self.cooldowns.pop(
                player_id,
                None,
            )
            return 0

        return math_ceil(remaining)

    def _get_blacklist_biomes(self) -> set[str]:
        configured = self.plugin.config_manager.get(
            "rtp.blacklist-biomes",
            [],
        )

        if not isinstance(configured, list):
            return set()

        return {
            self._normalize_identifier(value)
            for value in configured
            if isinstance(value, str)
            and value.strip()
        }

    def _get_number(
        self,
        path: str,
        default: int,
    ) -> int:
        value = self.plugin.config_manager.get(
            path,
            default,
        )

        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _is_same_position(
        self,
        first,
        second,
    ) -> bool:
        if first is None or second is None:
            return False

        if first.dimension != second.dimension:
            return False

        return (
            math_floor(first.x)
            == math_floor(second.x)
            and math_floor(first.z)
            == math_floor(second.z)
        )

    def _send(
        self,
        player,
        key: str,
        **placeholders,
    ) -> None:
        message = self.plugin.messages.get(
            key,
            **placeholders,
        )

        if message:
            player.send_message(message)

    @staticmethod
    def _normalize_identifier(
        identifier: str,
    ) -> str:
        return identifier.lower().strip().removeprefix(
            "minecraft:"
        )

    @staticmethod
    def _format_time(seconds: int) -> str:
        return str(max(1, seconds))


    def math_floor(value: float) -> int:
        return int(value // 1)
    
    
    def math_ceil(value: float) -> int:
        value = float(value)
        integer = int(value)
    
        if value == integer:
            return integer
    
        return integer + 1