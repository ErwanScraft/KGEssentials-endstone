from endstone.command import Command, CommandSender
from endstone.plugin import Plugin

from .utils.config import ConfigManager
from .utils.messages import KGEssentialsMessages

from .features.gamemode.handler import GamemodeHandler
from .features.spawn.handler import SpawnHandler
from .features.rtp.handler import RtpHandler


class KGEssentials(Plugin):
    api_version = "0.11"

    version = "0.2.0"
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
            "description": "Set the KGEssentials spawn.",
            "usages": ["/setspawn"],
            "permissions": ["kgessentials.setspawn"],
        },
        "rtp": {
            "description": "Teleport to a random safe location.",
            "usages": ["/rtp"],
            "permissions": ["kgessentials.rtp"],
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
        "kgessentials.rtp": {
            "description": "Allows the use of the random teleport command.",
            "default": "true",
        },
    }

    def on_enable(self) -> None:
        self._load_resources()
        self._load_configuration()
        self._load_messages()
        self._initialize_handlers()
        self._register_commands()
    
        self.register_events(self.rtp_handler)
    
        self.logger.info("KGEssentials enabled.")

    def _load_resources(self) -> None:
        self.save_resources("config.yml")
        self.save_resources("message.yml")
        self.save_resources("data/spawn.yml")

    def _load_configuration(self) -> None:
        self.config_manager = ConfigManager(self)
        self.config_manager.load()

        self.spawn_data = ConfigManager(
            self,
            "data/spawn.yml",
        )
        self.spawn_data.load()

        self.prefix = self.config_manager.get(
            "prefix",
            "KGEssentials",
        )

    def _load_messages(self) -> None:
        self.messages = KGEssentialsMessages(self)
        self.messages.load()

    def _initialize_handlers(self) -> None:
        self.gamemode_handler = GamemodeHandler(self)
        self.spawn_handler = SpawnHandler(self)
        self.rtp_handler = RtpHandler(self)

    def _register_commands(self) -> None:
        self._register_handler(
            (
                "gmc",
                "gms",
                "gma",
                "gmsp",
            ),
            self.gamemode_handler,
        )

        self._register_handler(
            (
                "spawn",
                "setspawn",
            ),
            self.spawn_handler,
        )

        self._register_handler(
            ("rtp",),
            self.rtp_handler,
        )

    def _register_handler(
        self,
        command_names: tuple[str, ...],
        handler,
    ) -> None:
        for command_name in command_names:
            command = self.get_command(command_name)

            if command is not None:
                command.executor = handler

    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: list[str],
    ) -> bool:
        return False