import time
import uuid

from backend.persistence.database import CypherDatabase


class AlarmRepository:
    KINDS = {"alarm", "timer", "reminder"}

    def __init__(self, database: CypherDatabase):
        self.database = database

    def create(self, *, kind: str, label: str, trigger_at: float) -> dict:
        if kind not in self.KINDS:
            raise ValueError("unsupported alarm kind")
        if trigger_at <= time.time():
            raise ValueError("trigger_at must be in the future")

        alarm_id = str(uuid.uuid4())
        now = time.time()
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO alarms (
                    id, kind, label, trigger_at, status, created_at
                ) VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (alarm_id, kind, label.strip() or "Cypher alarm", trigger_at, now),
            )
        return self.get(alarm_id)

    def get(self, alarm_id: str) -> dict | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM alarms WHERE id = ?",
                (alarm_id,),
            ).fetchone()
        return dict(row) if row else None

    def list(self) -> list[dict]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM alarms ORDER BY trigger_at ASC"
            ).fetchall()
        return [dict(row) for row in rows]

    def cancel(self, alarm_id: str) -> dict | None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                UPDATE alarms SET status = 'cancelled'
                WHERE id = ? AND status = 'pending'
                """,
                (alarm_id,),
            )
        return self.get(alarm_id)

    def claim_due(self, *, now: float | None = None) -> list[dict]:
        fired_at = now if now is not None else time.time()
        with self.database.transaction() as connection:
            rows = connection.execute(
                """
                SELECT * FROM alarms
                WHERE status = 'pending' AND trigger_at <= ?
                ORDER BY trigger_at ASC
                """,
                (fired_at,),
            ).fetchall()
            ids = [row["id"] for row in rows]
            for alarm_id in ids:
                connection.execute(
                    """
                    UPDATE alarms SET status = 'fired', fired_at = ?
                    WHERE id = ? AND status = 'pending'
                    """,
                    (fired_at, alarm_id),
                )
        return [self.get(alarm_id) for alarm_id in ids]

    def complete_fired(self) -> int:
        with self.database.transaction() as connection:
            cursor = connection.execute(
                "UPDATE alarms SET status = 'completed' WHERE status = 'fired'"
            )
        return cursor.rowcount
