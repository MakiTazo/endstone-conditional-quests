from endstone import asyncio as endstone_asyncio

command = {
    "questadmin": {
        "description": "Admin quest commands",
        "usages": [
            "/questadmin reload",
            "/questadmin complete <player: target> <quest_id: str>",
            "/questadmin unlock <player: target> <quest_id: str>",
            "/questadmin reset <player: target> <quest_id: str>"
        ],
        "permissions": ["endstone.command.questadmin"]
    }
}

def handler(plugin, sender, args):
    if len(args) == 0:
        sender.send_message("§cUsage: /questadmin reload | complete | unlock | reset")
        return True

    if args[0] == "reload":
        plugin.quest_manager.reload()
        sender.send_message("§aQuests reloaded!")
        return True

    if len(args) < 3:
        sender.send_message("§cUsage: /questadmin <complete|unlock|reset> <player> <quest_id|*>")
        return True

    target_player = plugin.server.get_player(args[1])
    if not target_player:
        sender.send_message(f"§cPlayer {args[1]} not found")
        return True

    from endstone_contitional_quests.models.player import QuestPlayer
    quest_player = QuestPlayer(str(target_player.unique_id), target_player.name, plugin.db, plugin.quest_manager)
    action = args[0]
    quest_id = args[2]

    async def run():
        await quest_player.load_all_progress()

        if action == "complete":
            quest = plugin.quest_manager.get_quest(quest_id)
            if not quest:
                sender.send_message(f"§cQuest {quest_id} not found")
                return
            quest_player.db.update_progress_async(quest_player.uuid, quest_id, quest_player.get_progress(quest_id)["target_progress"], True)
            quest_player.progress.setdefault(quest_id, {"target_progress": {}, "completed": False, "claimed": False, "unlocked": True})
            quest_player.progress[quest_id]["completed"] = True
            sender.send_message(f"§aCompleted {quest_id} for {target_player.name}")

        elif action == "unlock":
            if quest_id == "*":
                for quest in plugin.quest_manager.get_all_quests():
                    await quest_player.unlock_quest(quest.id)
                sender.send_message(f"§aUnlocked all quests for {target_player.name}")
            else:
                if not plugin.quest_manager.get_quest(quest_id):
                    sender.send_message(f"§cQuest {quest_id} not found")
                    return
                await quest_player.unlock_quest(quest_id)
                sender.send_message(f"§aUnlocked {quest_id} for {target_player.name}")

        elif action == "reset":
            if quest_id == "*":
                await quest_player.reset_all_quests()
                sender.send_message(f"§aReset all quests for {target_player.name}")
            else:
                if not plugin.quest_manager.get_quest(quest_id):
                    sender.send_message(f"§cQuest {quest_id} not found")
                    return
                await quest_player.reset_quest(quest_id)
                sender.send_message(f"§aReset {quest_id} for {target_player.name}")

    endstone_asyncio.submit(run())
    return True
