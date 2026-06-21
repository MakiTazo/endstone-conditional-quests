from endstone import Player
from endstone_conditional_quests.models.quest import Quest

class RewardHandler:
    def __init__(self, plugin):
        self.plugin = plugin

    def give_reward(self, player: Player, quest: Quest):
        reward = quest.reward

        if reward.type != "command":
            player.send_message(f"§cUnknown reward type: {reward.type}")
            return

        for command in reward.value:
            parsed = command.replace("{player}", player.name)
            self.plugin.server.dispatch_command(self.plugin.server.command_sender, parsed)

        player.send_message(f"§aReward claimed for quest: {quest.name}")
