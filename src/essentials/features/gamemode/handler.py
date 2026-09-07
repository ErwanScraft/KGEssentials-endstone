from endstone import GameMode, Player
from endstone.command import Command, CommandExecutor, CommandSender


class GamemodeHandler(CommandExecutor):
    MODES = {
        "gmc": GameMode.CREATIVE,
        "gms": GameMode.SURVIVAL,
        "gma": GameMode.ADVENTURE,
        "gmsp": GameMode.SPECTATOR,
    }

    MODE_NAMES = {
        GameMode.CREATIVE: "Creative",
        GameMode.SURVIVAL: "Survival",
        GameMode.ADVENTURE: "Adventure",
        GameMode.SPECTATOR: "Spectator",
    }

    def __init__(self, plugin) -> None:
        super().__init__()
        self.plugin = plugin

    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: list[str],
    ) -> bool:
        mode = self.MODES.get(command.name)

        if mode is None:
            return False

        if not isinstance(sender, Player):
            sender.send_message(
                self.plugin.messages.format("gamemode.player_only")
            )
            return False

        mode_name = self.MODE_NAMES[mode]

        if sender.game_mode == mode:
            sender.send_message(
                self.plugin.messages.format(
                    "gamemode.already",
                    mode=mode_name,
                )
            )
            return True

        sender.game_mode = mode

        sender.send_message(
            self.plugin.messages.format(
                "gamemode.changed",
                mode=mode_name,
            )
        )

        return True