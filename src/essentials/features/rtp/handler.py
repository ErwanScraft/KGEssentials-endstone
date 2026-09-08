import math
import random
import time

from endstone import Player
from endstone.command import (
    Command,
    CommandExecutor,
    CommandSender,
)
from endstone.level import Location


class RtpHandler(CommandExecutor):
    _DANGEROUS_BLOCKS = {
        "lava",
        "flowing_lava",
        "water",
        "flowing_water",
        "fire",
        "soul_fire",
        "cactus",
        "magma_block",
        "campfire",
        "soul_campfire",
        "powder_snow",
    }

    _PASSABLE_BLOCKS = {
        "air",
        "cave_air",
        "void_air",
        "short_grass",
        "tall_grass",
        "fern",
        "large_fern",
        "deadbush",
        "vine",
        "glow_lichen",
        "torch",
        "soul_torch",
        "redstone_torch",
        "flower",
        "dandelion",
        "poppy",
        "blue_orchid",
        "allium",
        "azure_bluet",
        "red_tulip",
        "orange_tulip",
        "white_tulip",
        "pink_tulip",
        "oxeye_daisy",
        "cornflower",
        "lily_of_the_valley",
        "wither_rose",
        "sunflower",
        "lilac",
        "rose_bush",
        "peony",
        "snow_layer",
    }

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
                self.plugin.messages.format(
                    "callback.player_only"
                )
            )
            return False

        if command.name == "rtp":
            return self._rtp(sender)

        return False

    def _rtp(
        self,
        player: Player,
    ) -> bool:
        cooldown = self._get_number(
            "rtp.cooldown",
            30.0,
        )
        radius = self._get_number(
            "rtp.radius",
            500.0,
        )
        attempts = int(
            self._get_number(
                "rtp.attempts",
                16.0,
            )
        )

        cooldown = max(0.0, cooldown)
        radius = max(1.0, radius)
        attempts = max(1, attempts)

        player_id = player.unique_id
        now = time.monotonic()
        last_used = self._cooldowns.get(player_id)

        if last_used is not None:
            remaining = cooldown - (now - last_used)

            if remaining > 0:
                player.send_message(
                    self.plugin.messages.format(
                        "rtp.cooldown",
                        time=max(1, math.ceil(remaining)),
                    )
                )
                return False

        location = player.location
        dimension = location.dimension

        for _ in range(attempts):
            target = self._find_safe_location(
                dimension,
                location.x,
                location.z,
                radius,
            )

            if target is None:
                continue

            if not player.teleport(target):
                continue

            if cooldown > 0:
                self._cooldowns[player_id] = time.monotonic()

            player.send_message(
                self.plugin.messages.format(
                    "rtp.teleported"
                )
            )

            return True

        player.send_message(
            self.plugin.messages.format(
                "rtp.failed"
            )
        )

        return False

    def _find_safe_location(
        self,
        dimension,
        origin_x: float,
        origin_z: float,
        radius: float,
    ):
        distance = math.sqrt(
            random.uniform(
                0.0,
                radius * radius,
            )
        )
        angle = random.uniform(
            0.0,
            math.tau,
        )

        x = origin_x + math.cos(angle) * distance
        z = origin_z + math.sin(angle) * distance

        block_x = math.floor(x)
        block_z = math.floor(z)

        try:
            ground_y = dimension.get_highest_block_y_at(
                block_x,
                block_z,
            )

            ground = dimension.get_block_at(
                block_x,
                ground_y,
                block_z,
            )
            feet = dimension.get_block_at(
                block_x,
                ground_y + 1,
                block_z,
            )
            head = dimension.get_block_at(
                block_x,
                ground_y + 2,
                block_z,
            )
        except (TypeError, ValueError):
            return None

        if ground is None or feet is None or head is None:
            return None

        ground_type = self._block_type(ground)
        feet_type = self._block_type(feet)
        head_type = self._block_type(head)

        if ground_type in self._DANGEROUS_BLOCKS:
            return None

        if feet_type not in self._PASSABLE_BLOCKS:
            return None

        if head_type not in self._PASSABLE_BLOCKS:
            return None

        return Location(
            dimension,
            block_x + 0.5,
            ground_y + 1.0,
            block_z + 0.5,
            0.0,
            0.0,
        )

    @staticmethod
    def _block_type(block) -> str:
        block_type = getattr(
            block,
            "type",
            "",
        )

        if not isinstance(block_type, str):
            return ""

        return block_type.removeprefix(
            "minecraft:"
        ).lower()

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
            return default