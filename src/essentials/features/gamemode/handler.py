from endstone import GameMode, Player
from endstone.command import Command, CommandExecutor, CommandSender


class GamemodeHandler(CommandExecutor):
    MODES = {
        "gmc": GameMode.Creative,
        "gms": GameMode.Survival,
        "gma": GameMode.Adventure,
        "gmsp": GameMode.Spectator,
    }

    MODE_NAMES = {
        GameMode.Creative: "Creative",
        GameMode.Survival: "Survival",
        GameMode.Adventure: "Adventure",
        GameMode.Spectator: "Spectator",
    }

    def __init__(self, plugin) -> None:
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
            sender.send_message(self.plugin.messages["player_only"])
            return False

        if sender.game_mode == mode:
            sender.send_message(
                self.plugin.messages["already_in_mode"].format(
                    mode=self.MODE_NAMES[mode]
                )
            )
            return True

        sender.game_mode = mode

        sender.send_message(
            self.plugin.messages["gamemode_changed"].format(
                mode=self.MODE_NAMES[mode]
            )
        )

        return True