import math
import random

from endstone.level import Location


class RtpService:
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

    _AIR_BLOCKS = {
        "air",
        "cave_air",
        "void_air",
    }

    _NON_SOLID_GROUND = {
        "short_grass",
        "tall_grass",
        "fern",
        "large_fern",
        "vine",
        "glow_lichen",
        "snow_layer",
        "leaves",
        "oak_leaves",
        "spruce_leaves",
        "birch_leaves",
        "jungle_leaves",
        "acacia_leaves",
        "dark_oak_leaves",
        "mangrove_leaves",
        "cherry_leaves",
        "azalea_leaves",
        "flowering_azalea_leaves",
    }

    def __init__(self, plugin) -> None:
        self.plugin = plugin

    def find_location(
        self,
        dimension,
        origin_x: float,
        origin_z: float,
        radius: float,
        attempts: int,
    ):
        for _ in range(attempts):
            location = self._generate_location(
                dimension,
                origin_x,
                origin_z,
                radius,
            )

            if location is not None:
                return location

        return None

    def _generate_location(
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

            below = dimension.get_block_at(
                block_x,
                ground_y - 1,
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
        except Exception as exc:
            self.plugin.logger.debug(
                f"RTP location check failed at "
                f"{block_x}, {block_z}: {exc}"
            )
            return None

        if any(
            block is None
            for block in (
                ground,
                below,
                feet,
                head,
            )
        ):
            return None

        ground_type = self._block_type(ground)
        below_type = self._block_type(below)
        feet_type = self._block_type(feet)
        head_type = self._block_type(head)

        # Ground must be a real solid block.
        if not self._is_valid_ground(ground_type):
            return None

        # Reject dangerous blocks below the player.
        if below_type in self._DANGEROUS_BLOCKS:
            return None

        # Player's body must have two clear blocks.
        if not self._is_passable(feet_type):
            return None

        if not self._is_passable(head_type):
            return None

        # Prevent spawning directly above dangerous blocks.
        if feet_type in self._DANGEROUS_BLOCKS:
            return None

        if head_type in self._DANGEROUS_BLOCKS:
            return None

        return Location(
            dimension,
            block_x + 0.5,
            ground_y + 1.0,
            block_z + 0.5,
            0.0,
            0.0,
        )

    @classmethod
    def _is_valid_ground(
        cls,
        block_type: str,
    ) -> bool:
        if not block_type:
            return False

        if block_type in cls._AIR_BLOCKS:
            return False

        if block_type in cls._DANGEROUS_BLOCKS:
            return False

        if block_type in cls._NON_SOLID_GROUND:
            return False

        if block_type.endswith("_leaves"):
            return False

        return True

    @classmethod
    def _is_passable(
        cls,
        block_type: str,
    ) -> bool:
        if block_type in cls._AIR_BLOCKS:
            return True

        return block_type in {
            "short_grass",
            "tall_grass",
            "fern",
            "large_fern",
            "vine",
            "glow_lichen",
            "snow_layer",
        }

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