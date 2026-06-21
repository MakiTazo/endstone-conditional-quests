from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from endstone_conditional_quests.commands import preloaded_commands, preloaded_handlers
from endstone_conditional_quests.core.config import Config
from endstone_conditional_quests.core.yaml_loader import QuestLoader
from endstone_conditional_quests.core.quest_manager import QuestManager
from endstone_conditional_quests.core.database import PlayerDatabase
from endstone_conditional_quests.gui.menus import QuestMenu
from endstone_conditional_quests.utils.reward_handler import RewardHandler
from endstone import asyncio as endstone_asyncio

class QuestsPlugin(Plugin):
    api_version = "0.11"
    depend = ["jwinventoryapi", "jwplaceholderapi"]
    commands = preloaded_commands
    handlers = preloaded_handlers

    def on_load(self):
        self.logger.info("Conditional Quests loading...")
        self.plugin_config = Config(str(self.data_folder))
        self.quest_loader = QuestLoader(self)
        self.quest_manager = QuestManager(self, self.quest_loader)
        self.db = PlayerDatabase(self.plugin_config, self.quest_manager)
        endstone_asyncio.submit(self.db.connect()).result()
        self.reward_handler = RewardHandler(self)
        self.quest_menu = QuestMenu(self, self.quest_manager, self.reward_handler)

    def on_enable(self):
        self.papi = self.server.plugin_manager.get_plugin("jwplaceholderapi")
        self.quest_manager.start_checker(period_ticks=20)
        self.register_events(self)
        self.logger.info("Conditional Quests enabled!")

    def on_disable(self):
        self.logger.info("QuestsPlugin disabled!")
        for menu in list(self.quest_menu.active_menus.values()):
            try:
                menu.close_all()
            except Exception:
                pass
        if self.db and self.db.connection:
            endstone_asyncio.submit(self.db.connection.close()).result()

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if command.name in self.handlers:
            return self.handlers[command.name](self, sender, args)
        return False
