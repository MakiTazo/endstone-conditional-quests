import os
import json
import aiosqlite
import aiomysql
from typing import Dict, Any
from endstone import asyncio as endstone_asyncio


class PlayerDatabase:
    def __init__(self, config, quest_manager):
        self.config = config
        self.quest_manager = quest_manager
        self.connection = None

    async def connect(self):
        if self.config.db_type == "sqlite":
            self.connection = await aiosqlite.connect(
                os.path.join(self.config.data_folder, "quests.db")
            )
        else:
            self.connection = await aiomysql.connect(
                host=self.config.mysql_host,
                port=self.config.mysql_port,
                user=self.config.mysql_user,
                password=self.config.mysql_password,
                db=self.config.mysql_database,
                autocommit=True
            )
        await self._init_db()

    async def _init_db(self):
        async with self.connection.cursor() as cursor:
            if self.config.db_type == "sqlite":
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS player_quests (
                        player_uuid TEXT,
                        quest_id TEXT,
                        target_progress TEXT DEFAULT '{}',
                        completed BOOLEAN DEFAULT 0,
                        claimed BOOLEAN DEFAULT 0,
                        unlocked BOOLEAN DEFAULT 0,
                        PRIMARY KEY (player_uuid, quest_id)
                    )
                """)
            else:
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS player_quests (
                        player_uuid VARCHAR(36),
                        quest_id VARCHAR(64),
                        target_progress TEXT DEFAULT '{}',
                        completed BOOLEAN DEFAULT 0,
                        claimed BOOLEAN DEFAULT 0,
                        unlocked BOOLEAN DEFAULT 0,
                        PRIMARY KEY (player_uuid, quest_id)
                    )
                """)
            await self.connection.commit()

    def _ph(self):
        return "?" if self.config.db_type == "sqlite" else "%s"

    async def get_progress(self, player_uuid: str, quest_id: str) -> Dict[str, Any]:
        ph = self._ph()
        async with self.connection.cursor() as cursor:
            await cursor.execute(f"""
                SELECT target_progress, completed, claimed, unlocked
                FROM player_quests
                WHERE player_uuid = {ph} AND quest_id = {ph}
            """, (player_uuid, quest_id))
            result = await cursor.fetchone()

        if result:
            return {
                "target_progress": json.loads(result[0]),
                "completed": bool(result[1]),
                "claimed": bool(result[2]),
                "unlocked": bool(result[3])
            }
        return {"target_progress": {}, "completed": False, "claimed": False, "unlocked": False}

    async def update_progress(self, player_uuid: str, quest_id: str, target_progress: Dict[str, int], completed: bool):
        progress_json = json.dumps(target_progress)
        async with self.connection.cursor() as cursor:
            if self.config.db_type == "sqlite":
                await cursor.execute("""
                    INSERT OR REPLACE INTO player_quests (player_uuid, quest_id, target_progress, completed, claimed, unlocked)
                    VALUES (?, ?, ?, ?,
                        COALESCE((SELECT claimed FROM player_quests WHERE player_uuid = ? AND quest_id = ?), 0),
                        COALESCE((SELECT unlocked FROM player_quests WHERE player_uuid = ? AND quest_id = ?), 0))
                """, (player_uuid, quest_id, progress_json, completed, player_uuid, quest_id, player_uuid, quest_id))
            else:
                await cursor.execute("""
                    INSERT INTO player_quests (player_uuid, quest_id, target_progress, completed, claimed, unlocked)
                    VALUES (%s, %s, %s, %s, 0, 0)
                    ON DUPLICATE KEY UPDATE target_progress = %s, completed = %s
                """, (player_uuid, quest_id, progress_json, completed, progress_json, completed))
            await self.connection.commit()

    async def mark_claimed(self, player_uuid: str, quest_id: str):
        ph = self._ph()
        async with self.connection.cursor() as cursor:
            await cursor.execute(f"""
                UPDATE player_quests SET claimed = 1
                WHERE player_uuid = {ph} AND quest_id = {ph}
            """, (player_uuid, quest_id))
            await self.connection.commit()

    async def unlock_quest(self, player_uuid: str, quest_id: str):
        async with self.connection.cursor() as cursor:
            if self.config.db_type == "sqlite":
                await cursor.execute("""
                    INSERT OR REPLACE INTO player_quests (player_uuid, quest_id, target_progress, completed, claimed, unlocked)
                    VALUES (?, ?,
                        COALESCE((SELECT target_progress FROM player_quests WHERE player_uuid = ? AND quest_id = ?), '{}'),
                        COALESCE((SELECT completed FROM player_quests WHERE player_uuid = ? AND quest_id = ?), 0),
                        COALESCE((SELECT claimed FROM player_quests WHERE player_uuid = ? AND quest_id = ?), 0),
                        1)
                """, (player_uuid, quest_id, player_uuid, quest_id, player_uuid, quest_id, player_uuid, quest_id))
            else:
                await cursor.execute("""
                    INSERT INTO player_quests (player_uuid, quest_id, target_progress, completed, claimed, unlocked)
                    VALUES (%s, %s, '{}', 0, 0, 1)
                    ON DUPLICATE KEY UPDATE unlocked = 1
                """, (player_uuid, quest_id))
            await self.connection.commit()

    async def reset_quest(self, player_uuid: str, quest_id: str):
        ph = self._ph()
        async with self.connection.cursor() as cursor:
            await cursor.execute(f"""
                UPDATE player_quests
                SET target_progress = '{{}}', completed = 0, claimed = 0
                WHERE player_uuid = {ph} AND quest_id = {ph}
            """, (player_uuid, quest_id))
            await self.connection.commit()

    async def reset_all_quests(self, player_uuid: str):
        ph = self._ph()
        async with self.connection.cursor() as cursor:
            await cursor.execute(f"""
                UPDATE player_quests
                SET target_progress = '{{}}', completed = 0, claimed = 0
                WHERE player_uuid = {ph}
            """, (player_uuid,))
            await self.connection.commit()

    async def get_all_player_quests(self, player_uuid: str) -> Dict[str, Dict]:
        ph = self._ph()
        async with self.connection.cursor() as cursor:
            await cursor.execute(f"""
                SELECT quest_id, target_progress, completed, claimed, unlocked
                FROM player_quests WHERE player_uuid = {ph}
            """, (player_uuid,))
            rows = await cursor.fetchall()

        results = {}
        for row in rows:
            results[row[0]] = {
                "target_progress": json.loads(row[1]),
                "completed": bool(row[2]),
                "claimed": bool(row[3]),
                "unlocked": bool(row[4])
            }
        return results

    def update_progress_async(self, player_uuid: str, quest_id: str, target_progress: Dict[str, int], completed: bool):
        endstone_asyncio.submit(self.update_progress(player_uuid, quest_id, target_progress, completed))

    def mark_claimed_async(self, player_uuid: str, quest_id: str):
        endstone_asyncio.submit(self.mark_claimed(player_uuid, quest_id))
