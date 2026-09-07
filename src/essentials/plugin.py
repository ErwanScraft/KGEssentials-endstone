from endstone.plugin import Plugin

from .features.gamemode.handler import GamemodeHandler
from .features.spawn.handler import SpawnHandler
from .utils.messages import DEFAULT_MESSAGES


class KGEssentials(Plugin):
    api_version = "0.11"

    version = "0.1.0"
    authors = ["ErwanScraft"]
    description = "Essential utilities for Endstone servers."
    prefix = "KGEssentials"

    commands = {
        "gmc": {
            "description": "Change your gamemode to Creative.",
            "usages": ["/gmc"],
            "permissions": ["kgessentials.gamemode"],
        },
        "gms": {
            "description": "Change your gamemode to Survival.",
            "usages": ["/gms"],
            "permissions": ["kgessentials.gamemode"],
        },
        "gma": {
            "description": "Change your gamemode to Adventure.",
            "usages": ["/gma"],
            "permissions": ["kgessentials.gamemode"],
        },
        "gmsp": {
            "description": "Change your gamemode to Spectator.",
            "usages": ["/gmsp"],
            "permissions": ["kgessentials.gamemode"],
        },
        "spawn": {
            "description": "Teleport to the server spawn.",
            "usages": ["/spawn"],
            "permissions": ["kgessentials.spawn"],
        },
    }

    permissions = {
        "kgessentials.gamemode": {
            "description": "Allows the use of KGEssentials gamemode commands.",
            "default": "op",
        },
        "kgessentials.spawn": {
            "description": "Allows the use of the spawn command.",
            "default": "true",
        },
    }

    def on_enable(self) -> None:
        self.messages = DEFAULT_MESSAGES.copy()

        self.gamemode_handler = GamemodeHandler(self)
        
        self.spawn_handler = SpawnHandler(self)

        for command_name in ("gmc", "gms", "gma", "gmsp"):
            command = self.get_command(command_name)

            if command is not None:
                command.executor = self.gamemode_handler

        self.logger.info("KGEssentials enabled.")