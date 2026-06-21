from endstone import Player
from endstone import asyncio as endstone_asyncio

command = {
    "quests": {
        "description": "Open quests menu",
        "usages": ["/quests"],
        "permissions": []
    }
}

def handler(plugin, sender, args):
    if not isinstance(sender, Player):
        sender.send_message("§cOnly players can use this command")
        return True

    from endstone_contitional_quests.models.player import QuestPlayer
    quest_player = QuestPlayer(str(sender.unique_id), sender.name, plugin.db, plugin.quest_manager)

    async def load_and_open():
        await quest_player.load_all_progress()
        plugin.server.scheduler.run_task(
            plugin,
            lambda: plugin.quest_menu.open_categories_menu(sender, quest_player),
            delay=0
        )

    endstone_asyncio.submit(load_and_open())
    return True
