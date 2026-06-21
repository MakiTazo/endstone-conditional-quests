from typing import Dict, List, Optional
from endstone import asyncio as endstone_asyncio
from endstone_conditional_quests.models.quest import Quest
from endstone_conditional_quests.utils.condition_parser import parse_condition, evaluate_condition

class QuestManager:
    def __init__(self, plugin, loader):
        self.plugin = plugin
        self.loader = loader
        self.categories: Dict[str, dict] = {}
        self._load()

    def _load(self):
        self.categories.clear()
        data = self.loader.load_quests()

        for category_id, category_data in data.items():
            quests = {}
            for quest_id, quest_data in category_data["quests"].items():
                quests[quest_id] = Quest(quest_id, quest_data)

            self.categories[category_id] = {
                "icon": category_data["icon"],
                "name": category_data["name"],
                "quests": quests
            }

    def reload(self):
        self._load()

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        for category in self.categories.values():
            if quest_id in category["quests"]:
                return category["quests"][quest_id]
        return None

    def get_all_quests(self) -> List[Quest]:
        quests = []
        for category in self.categories.values():
            quests.extend(category["quests"].values())
        return quests

    def get_available_quests(self) -> List[Quest]:
        return self.get_all_quests()

    def get_categories(self) -> Dict[str, dict]:
        return self.categories

    def start_checker(self, period_ticks: int = 20):
        self.plugin.server.scheduler.run_task(
            self.plugin, self._tick, delay=period_ticks, period=period_ticks
        )

    def _tick(self):
        endstone_asyncio.submit(self._check_all_players())

    async def _check_all_players(self):
        papi = self.plugin.papi
        if not papi:
            return

        from endstone_conditional_quests.models.player import QuestPlayer

        for player in self.plugin.server.online_players:
            uuid = str(player.unique_id)
            quest_player = QuestPlayer(uuid, player.name, self.plugin.db, self)
            await quest_player.load_all_progress()

            for quest in self.get_all_quests():
                progress = quest_player.get_progress(quest.id)
                if not progress["unlocked"] or progress["completed"] or progress["claimed"]:
                    continue

                target_progress = dict(progress["target_progress"])
                all_met = True

                for condition in quest.conditions:
                    parsed = parse_condition(condition)
                    if not parsed:
                        all_met = False
                        continue

                    placeholder, operator, expected = parsed
                    resolved = papi.set_placeholders(player, placeholder)
                    met = evaluate_condition(condition, resolved)
                    target_progress[condition] = resolved

                    if not met:
                        all_met = False

                if target_progress != progress["target_progress"] or all_met != progress["completed"]:
                    quest_player.db.update_progress_async(uuid, quest.id, target_progress, all_met)
                    quest_player.progress[quest.id]["target_progress"] = target_progress
                    quest_player.progress[quest.id]["completed"] = all_met

                    if all_met:
                        self.plugin.server.scheduler.run_task(
                            self.plugin,
                            lambda p=player, q=quest: p.send_message(f"§aQuest completed: {q.name}"),
                            delay=0
                        )
