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

    _PASSABLE_BLOCKS = {
        "short_grass",
        "tall_grass",
        "fern",
        "large_fern",
        "vine",
        "glow_lichen",
        "snow_layer",
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
                feet,
                head,
            )
        ):
            return None

        ground_type = self._block_type(ground)
        feet_type = self._block_type(feet)
        head_type = self._block_type(head)

        if not self._is_valid_ground(ground_type):
            return None

        if not self._is_passable(feet_type):
            return None

        if not self._is_passable(head_type):
            return None

        if not self._is_safe_landing(
            dimension,
            block_x,
            ground_y,
            block_z,
        ):
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
    def _is_safe_landing(
        cls,
        dimension,
        block_x: int,
        ground_y: int,
        block_z: int,
    ) -> bool:
        """
        Validate that the selected landing block has
        stable terrain immediately around the player.

        This is intentionally lightweight. It does not
        require every neighboring block to be identical
        or solid, only that the player is not landing on
        an exposed edge or dangerous terrain.
        """

        try:
            neighbors = (
                (block_x + 1, block_z),
                (block_x - 1, block_z),
                (block_x, block_z + 1),
                (block_x, block_z - 1),
            )

            for neighbor_x, neighbor_z in neighbors:
                neighbor_ground_y = (
                    dimension.get_highest_block_y_at(
                        neighbor_x,
                        neighbor_z,
                    )
                )

                if neighbor_ground_y < ground_y - 1:
                    continue

                block = dimension.get_block_at(
                    neighbor_x,
                    ground_y,
                    neighbor_z,
                )

                if block is None:
                    continue

                block_type = cls._block_type(block)

                if block_type in cls._DANGEROUS_BLOCKS:
                    return False

            return True

        except Exception:
            return True

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

        if block_type.endswith("_leaves"):
            return False

        return True

    @classmethod
    def _is_passable(
        cls,
        block_type: str,
    ) -> bool:
        if not block_type:
            return False

        if block_type in cls._AIR_BLOCKS:
            return True

        return block_type in cls._PASSABLE_BLOCKS

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