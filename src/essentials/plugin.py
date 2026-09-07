from endstone.plugin import Plugin

from .utils.config import KGEssentialsConfig
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
            "description": "Set the server spawn to your current location.",
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
            "description": "Allows setting the server spawn.",
            "default": "op",
        },
    }

    def on_enable(self) -> None:
        self.save_resources("config.yml")
        self.save_resources("message.yml")
    
        self._config_manager = KGEssentialsConfig(self)
        self._config_manager.load()
        self.config = self._config_manager
    
        self._messages = KGEssentialsMessages(self)
        self._messages.load()
        self.messages = self._messages
    
        self.prefix = self._config_manager.get("prefix", "KGEssentials")
    
        self.gamemode_handler = GamemodeHandler(self)
        self.spawn_handler = SpawnHandler(self)
        
        setspawn_command = self.get_command("setspawn")

        if setspawn_command is not None:
            setspawn_command.executor = self.spawn_handler
    
        for command_name in ("gmc", "gms", "gma", "gmsp"):
            command = self.get_command(command_name)
    
            if command is not None:
                command.executor = self.gamemode_handler
    
        spawn_command = self.get_command("spawn")
    
        if spawn_command is not None:
            spawn_command.executor = self.spawn_handler
    
        self.logger.info("KGEssentials enabled.")