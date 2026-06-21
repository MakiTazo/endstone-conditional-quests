import os
from ruamel.yaml import YAML

class QuestLoader:
    def __init__(self, plugin):
        self.plugin = plugin
        self.categories_path = os.path.join(plugin.data_folder, "categories")
        self.yaml = YAML()

    def load_quests(self) -> dict:
        os.makedirs(self.categories_path, exist_ok=True)

        if not os.listdir(self.categories_path):
            self._create_examples()

        categories = {}
        for filename in os.listdir(self.categories_path):
            if not filename.endswith(".yml"):
                continue

            category_id = filename[:-4]
            filepath = os.path.join(self.categories_path, filename)

            with open(filepath, "r", encoding="utf-8") as f:
                data = self.yaml.load(f)
                categories[category_id] = {
                    "icon": data.get("icon", "minecraft:paper"),
                    "name": data.get("name", category_id),
                    "quests": data.get("quests", {})
                }

        return categories

    def _create_examples(self):
        mobs = {
            "icon": "minecraft:zombie_spawn_egg",
            "name": "Mob Quests",
            "quests": {
                "villager_avenger": {
                    "name": "Villager Avenger",
                    "description": "All for the villagers",
                    "type": "kill_mob",
                    "target": {
                        "pillager": 500,
                        "ravager": 200,
                        "evoker": 50
                    },
                    "reward": {
                        "type": "command",
                        "value": "give {player} minecraft:emerald 500"
                    }
                },
                "zombie_slayer": {
                    "name": "Zombie Slayer",
                    "description": "Kill 50 zombies",
                    "type": "kill_mob",
                    "target": {
                        "zombie": 50
                    },
                    "reward": {
                        "type": "command",
                        "value": "give {player} minecraft:diamond 5"
                    }
                }
            }
        }

        blocks = {
            "icon": "minecraft:stone",
            "name": "Block Quests",
            "quests": {
                "stone_breaker": {
                    "name": "Stone Breaker",
                    "description": "Break 5000 stone blocks",
                    "type": "break_block",
                    "target": {
                        "stone": 5000
                    },
                    "reward": {
                        "type": "command",
                        "value": "give {player} minecraft:emerald 64"
                    }
                }
            }
        }

        for filename, data in [("mobs.yml", mobs), ("blocks.yml", blocks)]:
            filepath = os.path.join(self.categories_path, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                self.yaml.dump(data, f)

    def reload(self) -> dict:
        return self.load_quests()
