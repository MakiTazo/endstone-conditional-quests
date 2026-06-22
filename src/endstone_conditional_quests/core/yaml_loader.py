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
                "zombie_slayer_1": {
                    "name": "Zombie Slayer I",
                    "description": "Kill 500 zombies",
                    "conditions": [
                        "%jwstats_mob_kill_zombie% >= 500"
                    ],
                    "reward": {
                        "type": "command",
                        "value": [
                            "give {player} minecraft:diamond 64"
                        ]
                    }
                },
                "zombie_slayer_2": {
                    "name": "Zombie Slayer II",
                    "description": "Kill 1000 zombies",
                    "conditions": [
                        "%jwstats_mob_kill_zombie% >= 1000"
                    ],
                    "reward": {
                        "type": "command",
                        "value": [
                            "give {player} minecraft:emerald 124"
                        ]
                    }
                },
            }
        }

        blocks = {
            "icon": "minecraft:stone",
            "name": "Block Quests",
            "quests": {
                "stone_breaker": {
                    "name": "Stone Breaker",
                    "description": "Break 100 stone blocks",
                    "conditions": [
                        "%jwstats_block_break_stone% >= 100"
                    ],
                    "reward": {
                        "type": "command",
                        "value": [
                            "give {player} minecraft:emerald 3"
                        ]
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
