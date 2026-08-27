import time
import uuid

from backend.persistence.database import CypherDatabase


class MemoryRepository:
    def __init__(self, database: CypherDatabase):
        self.database = database

    def remember(
        self,
        *,
        content: str,
        category: str = "general",
        importance: float = 0.5,
        source: str | None = None,
    ) -> dict:
        clean_content = content.strip()
        clean_category = category.strip()
        if not clean_content:
            raise ValueError("memory content cannot be empty")
        if not clean_category:
            raise ValueError("memory category cannot be empty")
        if isinstance(importance, bool) or not 0.0 <= importance <= 1.0:
            raise ValueError("importance must be between 0 and 1")

        memory_id = str(uuid.uuid4())
        now = time.time()
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO memories (
                    id, category, content, importance, source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory_id,
                    clean_category,
                    clean_content,
                    importance,
                    source,
                    now,
                    now,
                ),
            )
        return self.get(memory_id)

    def get(self, memory_id: str) -> dict | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM memories WHERE id = ?",
                (memory_id,),
            ).fetchone()
        return dict(row) if row else None

    def recall(
        self,
        *,
        category: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        safe_limit = max(1, min(limit, 100))
        with self.database.connect() as connection:
            if category:
                rows = connection.execute(
                    """
                    SELECT * FROM memories
                    WHERE category = ?
                    ORDER BY importance DESC, updated_at DESC
                    LIMIT ?
                    """,
                    (category, safe_limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM memories
                    ORDER BY importance DESC, updated_at DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
        return [dict(row) for row in rows]
