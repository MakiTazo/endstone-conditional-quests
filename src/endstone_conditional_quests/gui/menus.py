from endstone import Player
from endstone.inventory import ItemStack
from jwinventoryapi import Menu, MenuType
from endstone_quests.models.quest import Quest
from endstone_quests.models.player import QuestPlayer
from endstone_quests.utils.condition_parser import parse_condition

SLOTS_PER_PAGE = 45
NAV_BARRIER_SLOTS = [45, 46, 48, 50, 52]
NAV_PREV = 47
NAV_PAGE = 49
NAV_NEXT = 51
NAV_BACK = 53

class QuestMenu:
    def __init__(self, plugin, quest_manager, reward_handler):
        self.plugin = plugin
        self.quest_manager = quest_manager
        self.reward_handler = reward_handler
        self.active_menus = {}

    def _barrier(self) -> ItemStack:
        item = ItemStack("minecraft:barrier")
        meta = item.item_meta
        meta.display_name = "§r"
        item.set_item_meta(meta)
        return item

    def _on_menu_close(self, player: Player):
        uid = str(player.unique_id)
        if uid in self.active_menus:
            del self.active_menus[uid]

    def _fill_nav(self, menu: Menu, page: int, total_pages: int, on_prev, on_next, on_back, show_back: bool = True):
        barrier = self._barrier()
        for slot in NAV_BARRIER_SLOTS:
            menu.set_item(slot, barrier)

        prev_item = ItemStack("minecraft:arrow")
        meta = prev_item.item_meta
        meta.display_name = "§ePrev Page"
        prev_item.set_item_meta(meta)
        if page > 0:
            menu.set_item(NAV_PREV, prev_item, on_click=on_prev)
        else:
            menu.set_item(NAV_PREV, barrier)

        page_item = ItemStack("minecraft:paper")
        meta = page_item.item_meta
        meta.display_name = f"§fPage {page + 1}/{total_pages}"
        page_item.set_item_meta(meta)
        menu.set_item(NAV_PAGE, page_item)

        next_item = ItemStack("minecraft:arrow")
        meta = next_item.item_meta
        meta.display_name = "§eNext Page"
        next_item.set_item_meta(meta)
        if page < total_pages - 1:
            menu.set_item(NAV_NEXT, next_item, on_click=on_next)
        else:
            menu.set_item(NAV_NEXT, barrier)

        if show_back:
            back_item = ItemStack("minecraft:magma_cream")
            meta = back_item.item_meta
            meta.display_name = "§cBack"
            back_item.set_item_meta(meta)
            menu.set_item(NAV_BACK, back_item, on_click=on_back)
        else:
            menu.set_item(NAV_BACK, barrier)

    def open_categories_menu(self, player: Player, quest_player: QuestPlayer, page: int = 0):
        categories = list(self.quest_manager.get_categories().items())
        total_pages = max(1, -(-len(categories) // SLOTS_PER_PAGE))
        start = page * SLOTS_PER_PAGE
        page_categories = categories[start:start + SLOTS_PER_PAGE]

        menu = Menu(MenuType.DOUBLE_CHEST, "§6Quests")

        for slot, (category_id, category) in enumerate(page_categories):
            item = ItemStack(category["icon"])
            meta = item.item_meta
            meta.display_name = f"§6{category['name']}"
            item.set_item_meta(meta)

            def make_handler(cid=category_id):
                def handler(p, s, i, inv):
                    self.active_menus[str(p.unique_id)].close(p)
                    self.open_quests_menu(p, quest_player, cid)
                return handler

            menu.set_item(slot, item, on_click=make_handler())

        self._fill_nav(
            menu, page, total_pages,
            on_prev=lambda p, s, i, inv: self._reopen_categories(p, quest_player, page - 1),
            on_next=lambda p, s, i, inv: self._reopen_categories(p, quest_player, page + 1),
            on_back=lambda p, s, i, inv: None,
            show_back=False
        )

        menu.set_close_listener(self._on_menu_close)
        menu.send_to(player)
        self.active_menus[str(player.unique_id)] = menu

    def _reopen_categories(self, player: Player, quest_player: QuestPlayer, page: int):
        uid = str(player.unique_id)
        if uid in self.active_menus:
            self.active_menus[uid].close(player)
        self.open_categories_menu(player, quest_player, page)

    def open_quests_menu(self, player: Player, quest_player: QuestPlayer, category_id: str, page: int = 0):
        category = self.quest_manager.get_categories().get(category_id)
        if not category:
            return

        quests = list(category["quests"].values())
        total_pages = max(1, -(-len(quests) // SLOTS_PER_PAGE))
        start = page * SLOTS_PER_PAGE
        page_quests = quests[start:start + SLOTS_PER_PAGE]

        menu = Menu(MenuType.DOUBLE_CHEST, f"§6{category['name']}")

        for slot, quest in enumerate(page_quests):
            progress_data = quest_player.get_progress(quest.id)
            item = self._create_quest_item(quest, progress_data)

            def make_click_handler(q=quest, qp=quest_player):
                return lambda p, s, i, inv: self._handle_click(p, q, qp, category_id, page)

            menu.set_item(slot, item, on_click=make_click_handler())

        self._fill_nav(
            menu, page, total_pages,
            on_prev=lambda p, s, i, inv: self._reopen_quests(p, quest_player, category_id, page - 1),
            on_next=lambda p, s, i, inv: self._reopen_quests(p, quest_player, category_id, page + 1),
            on_back=lambda p, s, i, inv: self._reopen_back(p, quest_player)
        )

        menu.set_close_listener(self._on_menu_close)
        menu.send_to(player)
        self.active_menus[str(player.unique_id)] = menu

    def _reopen_quests(self, player: Player, quest_player: QuestPlayer, category_id: str, page: int):
        uid = str(player.unique_id)
        if uid in self.active_menus:
            self.active_menus[uid].close(player)
        self.open_quests_menu(player, quest_player, category_id, page)

    def _reopen_back(self, player: Player, quest_player: QuestPlayer):
        uid = str(player.unique_id)
        if uid in self.active_menus:
            self.active_menus[uid].close(player)
        self.open_categories_menu(player, quest_player)

    def _create_quest_item(self, quest: Quest, progress_data: dict) -> ItemStack:
        item = ItemStack("minecraft:paper")
        meta = item.item_meta
        meta.display_name = f"§6{quest.name}"

        lore = [f"§7{quest.description}"]

        if progress_data["completed"]:
            lore.append("§aCompleted")
        elif not progress_data["unlocked"]:
            lore.append("§cLocked")
        else:
            for condition in quest.conditions:
                parsed = parse_condition(condition)
                resolved = progress_data["target_progress"].get(condition, "0")
                if parsed:
                    _, operator, expected = parsed
                    lore.append(f"§e{resolved}/{expected:g}")
                else:
                    lore.append(f"§e{resolved}")

        if progress_data["claimed"]:
            lore.append("§7[Claimed]")

        lore.append(f"§bReward: {', '.join(quest.reward.value)}")
        meta.lore = lore
        item.set_item_meta(meta)
        return item

    def _handle_click(self, player: Player, quest: Quest, quest_player: QuestPlayer, category_id: str, page: int):
        progress = quest_player.get_progress(quest.id)

        if progress["claimed"]:
            player.send_message("§cYa reclamaste esta misión, no puedes volverla a reclamar.")
            return

        if quest_player.can_claim(quest.id):
            self.reward_handler.give_reward(player, quest)
            quest_player.claim_reward(quest.id)
            uid = str(player.unique_id)
            if uid in self.active_menus:
                self.active_menus[uid].close(player)
            self.open_quests_menu(player, quest_player, category_id, page)
        else:
            player.send_message("§cAún no has completado esta misión.")