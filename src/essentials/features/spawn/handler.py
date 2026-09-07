from endstone import Player
from endstone.command import Command, CommandExecutor, CommandSender


class SpawnHandler(CommandExecutor):
    def __init__(self, plugin) -> None:
        self.plugin = plugin

    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: list[str],
    ) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(self.plugin.messages["player_only"])
            return False

        spawn = sender.world.spawn_location

        if spawn is None:
            sender.send_message(self.plugin.messages["spawn_unavailable"])
            return False

        sender.teleport(spawn)

        sender.send_message(self.plugin.messages["teleported_to_spawn"])

        return True