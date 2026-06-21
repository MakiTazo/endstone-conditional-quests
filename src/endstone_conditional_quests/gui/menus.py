from endstone import Player
from endstone.inventory import ItemStack
from jwinventoryapi import Menu, MenuType
from endstone_conditional_quests.models.quest import Quest
from endstone_conditional_quests.models.player import QuestPlayer
from endstone_conditional_quests.utils.condition_parser import parse_condition

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

    def _close_active(self, player: Player):
        uid = str(player.unique_id)
        menu = self.active_menus.get(uid)
        if menu:
            menu.close(player)

    def _fill_nav(self, menu: Menu, page: int, total_pages: int, on_prev, on_next, on_back, show_back: bool = True):
        for slot in NAV_BARRIER_SLOTS:
            menu.set_item(slot, self._barrier())

        prev_item = ItemStack("minecraft:arrow")
        meta = prev_item.item_meta
        meta.display_name = "§ePrev Page"
        prev_item.set_item_meta(meta)
        if page > 0:
            menu.set_item(NAV_PREV, prev_item, on_click=on_prev)
        else:
            menu.set_item(NAV_PREV, self._barrier())

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
            menu.set_item(NAV_NEXT, self._barrier())

        if show_back:
            back_item = ItemStack("minecraft:magma_cream")
            meta = back_item.item_meta
            meta.display_name = "§cBack"
            back_item.set_item_meta(meta)
            menu.set_item(NAV_BACK, back_item, on_click=on_back)
        else:
            menu.set_item(NAV_BACK, self._barrier())

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
                    self._open_quests(p, quest_player, cid)
                    return True
                return handler

            menu.set_item(slot, item, on_click=make_handler())

        def on_prev(p, s, i, inv):
            self._open_categories(p, quest_player, page - 1)
            return True

        def on_next(p, s, i, inv):
            self._open_categories(p, quest_player, page + 1)
            return True

        self._fill_nav(
            menu, page, total_pages,
            on_prev=on_prev,
            on_next=on_next,
            on_back=lambda p, s, i, inv: True,
            show_back=False
        )

        menu.send_to(player)
        self.active_menus[str(player.unique_id)] = menu

    def _open_categories(self, player: Player, quest_player: QuestPlayer, page: int):
        self._close_active(player)
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
                def handler(p, s, i, inv):
                    self._handle_click(p, q, qp, category_id, page)
                    return True
                return handler

            menu.set_item(slot, item, on_click=make_click_handler())

        def on_prev(p, s, i, inv):
            self._open_quests(p, quest_player, category_id, page - 1)
            return True

        def on_next(p, s, i, inv):
            self._open_quests(p, quest_player, category_id, page + 1)
            return True

        def on_back(p, s, i, inv):
            self._open_categories(p, quest_player, 0)
            return True

        self._fill_nav(
            menu, page, total_pages,
            on_prev=on_prev,
            on_next=on_next,
            on_back=on_back
        )

        menu.send_to(player)
        self.active_menus[str(player.unique_id)] = menu

    def _open_quests(self, player: Player, quest_player: QuestPlayer, category_id: str, page: int = 0):
        self._close_active(player)
        self.open_quests_menu(player, quest_player, category_id, page)

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
            player.play_sound(player.location, "mob.villager.no", volume=1.0, pitch=1.0)
            return

        if quest_player.can_claim(quest.id):
            self.reward_handler.give_reward(player, quest)
            quest_player.claim_reward(quest.id)
            self._open_quests(player, quest_player, category_id, page)
        else:
            player.play_sound(player.location, "mob.villager.no", volume=1.0, pitch=1.0)