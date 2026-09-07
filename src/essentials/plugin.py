from endstone.command import Command, CommandSender
from endstone.plugin import Plugin

from .utils.config import ConfigManager
from .utils.messages import KGEssentialsMessages

from .features.gamemode.handler import GamemodeHandler
from .features.spawn.handler import SpawnHandler


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
        "setspawn": {
            "description": "Set the KGEssentials spawn to your current location.",
            "usages": ["/setspawn"],
            "permissions": ["kgessentials.setspawn"],
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
        "kgessentials.setspawn": {
            "description": "Allows setting the KGEssentials spawn.",
            "default": "op",
        },
    }

    def on_enable(self) -> None:
        self.save_resources("config.yml")
        self.save_resources("message.yml")
        self.save_resources("spawn.yml")

        self.config = ConfigManager(self)
        self.config.load()

        self.spawn_config = ConfigManager(
            self,
            "spawn.yml",
        )
        self.spawn_config.load()

        self._messages = KGEssentialsMessages(self)
        self._messages.load()
        self.messages = self._messages

        self.prefix = self.config.get(
            "prefix",
            "KGEssentials",
        )

        self.gamemode_handler = GamemodeHandler(self)
        self.spawn_handler = SpawnHandler(self)

        for command_name in (
            "gmc",
            "gms",
            "gma",
            "gmsp",
        ):
            command = self.get_command(command_name)

            if command is not None:
                command.executor = self.gamemode_handler

        for command_name in (
            "spawn",
            "setspawn",
        ):
            command = self.get_command(command_name)

            if command is not None:
                command.executor = self.spawn_handler

        self.logger.info("KGEssentials enabled.")

    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: list[str],
    ) -> bool:
        return False