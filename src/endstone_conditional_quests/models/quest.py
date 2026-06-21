from typing import Dict, Any, List

class Reward:
    def __init__(self, data: Dict[str, Any]):
        self.type = data.get("type", "command")
        value = data.get("value", [])
        self.value: List[str] = value if isinstance(value, list) else [value]


class Quest:
    def __init__(self, quest_id: str, data: Dict[str, Any]):
        self.id = quest_id
        self.name = data.get("name", quest_id)
        self.description = data.get("description", "")
        self.conditions: List[str] = data.get("conditions", [])
        self.reward = Reward(data.get("reward", {}))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions
        }
