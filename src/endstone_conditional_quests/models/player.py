from typing import Dict
from endstone_contitional_quests.core.database import PlayerDatabase

class QuestPlayer:
    def __init__(self, uuid: str, name: str, database: PlayerDatabase, quest_manager):
        self.uuid = uuid
        self.name = name
        self.db = database
        self.quest_manager = quest_manager
        self.progress: Dict[str, dict] = {}

    async def load_all_progress(self) -> Dict[str, dict]:
        self.progress = await self.db.get_all_player_quests(self.uuid)
        return self.progress

    def get_progress(self, quest_id: str) -> dict:
        return self.progress.get(quest_id, {
            "target_progress": {}, "completed": False, "claimed": False, "unlocked": False
        })

    def update_progress(self, quest_id: str, target: str, amount: int):
        quest = self.quest_manager.get_quest(quest_id)
        if not quest:
            return

        current = self.get_progress(quest_id)
        if not current["unlocked"] or current["completed"] or current["claimed"]:
            return

        target_progress = dict(current["target_progress"])
        required = quest.target.get(target, 0)
        target_progress[target] = min(amount, required)

        completed = all(
            target_progress.get(t, 0) >= req
            for t, req in quest.target.items()
        )

        self.db.update_progress_async(self.uuid, quest_id, target_progress, completed)
        self.progress[quest_id] = {
            "target_progress": target_progress,
            "completed": completed,
            "claimed": False,
            "unlocked": True
        }

    def can_claim(self, quest_id: str) -> bool:
        data = self.get_progress(quest_id)
        return data["unlocked"] and data["completed"] and not data["claimed"]

    def claim_reward(self, quest_id: str) -> bool:
        if not self.can_claim(quest_id):
            return False
        quest = self.quest_manager.get_quest(quest_id)
        if not quest:
            return False
        self.db.mark_claimed_async(self.uuid, quest_id)
        self.progress[quest_id]["claimed"] = True
        return True

    async def unlock_quest(self, quest_id: str):
        await self.db.unlock_quest(self.uuid, quest_id)
        if quest_id in self.progress:
            self.progress[quest_id]["unlocked"] = True
        else:
            self.progress[quest_id] = {
                "target_progress": {}, "completed": False, "claimed": False, "unlocked": True
            }

    async def reset_quest(self, quest_id: str):
        await self.db.reset_quest(self.uuid, quest_id)
        if quest_id in self.progress:
            self.progress[quest_id].update({"target_progress": {}, "completed": False, "claimed": False})

    async def reset_all_quests(self):
        await self.db.reset_all_quests(self.uuid)
        for quest_id in self.progress:
            self.progress[quest_id].update({"target_progress": {}, "completed": False, "claimed": False})
