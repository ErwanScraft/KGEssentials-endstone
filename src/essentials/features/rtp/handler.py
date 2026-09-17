import math
import time
from uuid import UUID

from endstone.command import Command, CommandExecutor, CommandSender
from endstone.event import PlayerMoveEvent, event_handler
from endstone.plugin import Plugin

from endstone import Player

from .service import RtpService


class RtpHandler(CommandExecutor):
    def __init__(self, plugin: Plugin) -> None:
        super().__init__()

        self.plugin = plugin
        self.service = RtpService(plugin)

        self.cooldowns: dict[UUID, float] = {}
        self.warmups: dict[UUID, dict] = {}

    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: list[str],
    ) -> bool:
        if not isinstance(sender, Player):
            self._send(
                sender,
                "callback.player_only",
            )
            return False
        
        player = sender
        player_id = player.unique_id

        if player_id in self.warmups:
            return True

        if not self._has_cooldown_bypass(player):
        remaining = self._get_cooldown_remaining(
            player_id
        )
    
        if remaining > 0:
            self._send(
                player,
                "rtp.cooldown",
                time=remaining,
            )
            return True

        self._start_warmup(player)

        return True

    def _start_warmup(self, player) -> None:
        player_id = player.unique_id

        warmup = max(
            0,
            self._get_int(
                "rtp.warmup",
                5,
            ),
        )

        if warmup <= 0:
            self._execute_rtp(player)
            return

        location = player.location
        
        state = {
            "location": (
                location.dimension,
                math.floor(location.x),
                math.floor(location.z),
            ),
            "remaining": warmup,
            "task": None,
        }

        self.warmups[player_id] = state

        self._send_actionbar(
            player,
            "rtp.warmup",
            time=warmup,
        )

        self._play_sound(
            player,
            "rtp.sounds.countdown",
        )

        state["task"] = self.plugin.server.scheduler.run_task(
            self.plugin,
            lambda: self._warmup_tick(player_id),
            delay=20,
            period=20,
        )

    def _warmup_tick(
        self,
        player_id: UUID,
    ) -> None:
        state = self.warmups.get(player_id)

        if state is None:
            return

        player = self.plugin.server.get_player(
            player_id
        )

        if player is None:
            self._cancel_warmup(player_id)
            return

        if not self._same_block_position(
            player.location,
            state["location"],
        ):
            self._cancel_warmup(
                player_id,
                notify=True,
            )
            return

        state["remaining"] -= 1

        if state["remaining"] <= 0:
            self._finish_warmup(player_id)
            return

        self._send_actionbar(
            player,
            "rtp.warmup",
            time=state["remaining"],
        )

        self._play_sound(
            player,
            "rtp.sounds.countdown",
        )

    def _finish_warmup(
        self,
        player_id: UUID,
    ) -> None:
        state = self.warmups.pop(
            player_id,
            None,
        )

        if state is None:
            return

        task = state["task"]

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
        player_id: UUID,
        notify: bool = False,
    ) -> None:
        state = self.warmups.pop(
            player_id,
            None,
        )

        if state is None:
            return

        task = state["task"]

        if task is not None:
            task.cancel()

        if not notify:
            return

        player = self.plugin.server.get_player(
            player_id
        )

        if player is None:
            return

        self._send(
            player,
            "rtp.cancelled",
        )

        self._play_sound(
            player,
            "rtp.sounds.cancelled",
        )

    def _execute_rtp(self, player) -> None:
        player_id = player.unique_id
        location = player.location

        radius = self._get_player_radius(player)

        attempts = self._get_int(
            "rtp.attempts",
            32,
        )

        blacklist_biomes = self._get_blacklist_biomes()

        target = self.service.find_location(
            location.dimension,
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

            self._play_sound(
                player,
                "rtp.sounds.failed",
            )

            return

        try:
            success = player.teleport(target)
        except Exception as exc:
            self.plugin.logger.debug(
                f"RTP teleport failed for "
                f"{player.name}: {exc}"
            )
            success = False

        if not success:
            self._send(
                player,
                "rtp.failed",
            )

            self._play_sound(
                player,
                "rtp.sounds.failed",
            )

            return

        if not self._has_cooldown_bypass(player):
        cooldown = max(
            0,
            self._get_int(
                "rtp.cooldown",
                30,
            ),
        )
    
        if cooldown > 0:
            self.cooldowns[player_id] = (
                time.monotonic() + cooldown
            )

        self._send(
            player,
            "rtp.teleported",
        )

        self._play_sound(
            player,
            "rtp.sounds.success",
        )

    def _play_sound(
        self,
        player,
        path: str,
    ) -> None:
        sound = self.plugin.config_manager.get(
            f"{path}.sound",
            "",
        )

        if not isinstance(sound, str) or not sound.strip():
            return

        volume = self._get_float(
            f"{path}.volume",
            1.0,
        )

        pitch = self._get_float(
            f"{path}.pitch",
            1.0,
        )

        try:
            player.play_sound(
                player.location,
                sound,
                volume,
                pitch,
            )
        except Exception as exc:
            self.plugin.logger.debug(
                f"RTP sound failed for "
                f"{player.name}: {exc}"
            )

    @event_handler
    def on_player_move(
        self,
        event: PlayerMoveEvent,
    ) -> None:
        player = event.player
        player_id = player.unique_id

        state = self.warmups.get(player_id)

        if state is None:
            return

        if not self._same_block_position(
            player.location,
            state["location"],
        ):
            self._cancel_warmup(
                player_id,
                notify=True,
            )
            
    def _has_cooldown_bypass(self, player) -> bool:
        return player.has_permission(
            "kgessentials.rtp.cooldown.bypass"
        )

    def _get_player_radius(self, player) -> int:
        default_radius = max(
            0,
            self._get_int(
                "rtp.radius",
                500,
            ),
        )

        configured = self.plugin.config_manager.get(
            "rtp.radius-permissions",
            {},
        )

        if not isinstance(configured, dict):
            return default_radius

        radius = default_radius

        for permission, value in configured.items():
            if not isinstance(permission, str):
                continue

            try:
                configured_radius = int(value)
            except (TypeError, ValueError):
                continue

            if configured_radius <= radius:
                continue

            if player.has_permission(permission):
                radius = configured_radius

        return radius

    def _get_cooldown_remaining(
        self,
        player_id: UUID,
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

        return math.ceil(remaining)

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

    def _get_int(
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

    def _get_float(
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
            return default
    
    def shutdown(self) -> None:
        for state in self.warmups.values():
            task = state.get("task")
    
            if task is not None:
                task.cancel()
    
        self.warmups.clear()
        self.cooldowns.clear()

    @staticmethod
    def _same_block_position(
        location,
        snapshot,
    ) -> bool:
        if location is None or snapshot is None:
            return False
    
        dimension, x, z = snapshot
    
        return (
            location.dimension == dimension
            and math.floor(location.x) == x
            and math.floor(location.z) == z
        )

    def _send(
        self,
        sender,
        key: str,
        **placeholders,
    ) -> None:
        message = self.plugin.messages.get(
            key,
            **placeholders,
        )

        if message:
            sender.send_message(message)

    def _send_actionbar(
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
            player.send_tip(message)

    @staticmethod
    def _normalize_identifier(
        identifier: str,
    ) -> str:
        return (
            identifier
            .lower()
            .strip()
            .removeprefix("minecraft:")
        )
    