import time
import uuid

from backend.persistence.database import CypherDatabase


class ConversationRepository:
    ROLES = {"system", "user", "assistant", "tool"}

    def __init__(self, database: CypherDatabase):
        self.database = database

    def create(self, *, title: str | None = None) -> dict:
        conversation_id = str(uuid.uuid4())
        now = time.time()
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (conversation_id, title, now, now),
            )
        return self.get(conversation_id)

    def add_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
    ) -> dict:
        if role not in self.ROLES:
            raise ValueError("unsupported conversation role")
        clean_content = content.strip()
        if not clean_content:
            raise ValueError("message content cannot be empty")

        message_id = str(uuid.uuid4())
        now = time.time()
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO messages (
                    id, conversation_id, role, content, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (message_id, conversation_id, role, clean_content, now),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )
        return {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": clean_content,
            "created_at": now,
        }

    def get(self, conversation_id: str) -> dict | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
        return dict(row) if row else None

    def history(self, conversation_id: str, *, limit: int = 50) -> list[dict]:
        safe_limit = max(1, min(limit, 200))
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (conversation_id, safe_limit),
            ).fetchall()
        return [dict(row) for row in rows]
