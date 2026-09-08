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
        blacklist_biomes: set[str] | None = None,
    ):
        blacklist_biomes = blacklist_biomes or set()

        radius = max(1.0, float(radius))
        attempts = max(1, int(attempts))

        for _ in range(attempts):
            target = self._generate_location(
                dimension,
                origin_x,
                origin_z,
                radius,
                blacklist_biomes,
            )

            if target is not None:
                return target

        return None

    def _generate_location(
        self,
        dimension,
        origin_x: float,
        origin_z: float,
        radius: float,
        blacklist_biomes: set[str],
    ):
        distance = math.sqrt(
            random.uniform(0.0, radius * radius)
        )

        angle = random.uniform(
            0.0,
            math.tau,
        )

        block_x = math.floor(
            origin_x + math.cos(angle) * distance
        )

        block_z = math.floor(
            origin_z + math.sin(angle) * distance
        )

        try:
            ground = dimension.get_highest_block_at(
                block_x,
                block_z,
            )

            if ground is None:
                return None

            ground_y = ground.y

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

        if feet is None or head is None:
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

        if not self._is_valid_biome(
            ground,
            blacklist_biomes,
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
    def _is_valid_biome(
        cls,
        block,
        blacklist_biomes: set[str],
    ) -> bool:
        if not blacklist_biomes:
            return True

        try:
            biome = block.biome

            if biome is None:
                return True

            biome_id = cls._normalize_identifier(
                biome.id
            )

            return biome_id not in blacklist_biomes

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

    @staticmethod
    def _normalize_identifier(identifier) -> str:
        return str(identifier).lower().strip().removeprefix(
            "minecraft:"
        )