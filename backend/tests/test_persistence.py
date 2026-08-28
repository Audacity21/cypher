import time

from backend.persistence.alarm_repository import AlarmRepository
from backend.persistence.conversation_repository import ConversationRepository
from backend.persistence.database import CypherDatabase, SCHEMA_VERSION
from backend.persistence.memory_repository import MemoryRepository


def test_schema_creates_every_v1_domain(tmp_path):
    database = CypherDatabase(tmp_path / "cypher.db")

    with database.connect() as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        version = connection.execute(
            "SELECT version FROM schema_version"
        ).fetchone()["version"]

    assert {
        "conversations",
        "messages",
        "memories",
        "alarms",
        "events",
        "tool_runs",
        "settings",
    } <= tables
    assert version == SCHEMA_VERSION


def test_memory_survives_database_reopen(tmp_path):
    path = tmp_path / "cypher.db"
    first = MemoryRepository(CypherDatabase(path))
    saved = first.remember(
        content="The user's preferred wake time is 6 AM.",
        category="preference",
        importance=0.9,
        source="conversation",
    )

    reopened = MemoryRepository(CypherDatabase(path))
    recalled = reopened.recall(category="preference")

    assert recalled == [saved]


def test_memory_deduplicates_and_retrieves_relevant_fact(tmp_path):
    memories = MemoryRepository(CypherDatabase(tmp_path / "cypher.db"))
    first = memories.remember(content="Ankit prefers concise answers")
    second = memories.remember(content="Ankit prefers concise answers", importance=0.9)
    memories.remember(content="Ankit likes cyan lighting")
    assert first["id"] == second["id"]
    assert memories.recall_relevant("How should answers be written?")[0]["id"] == first["id"]


def test_conversation_history_survives_database_reopen(tmp_path):
    path = tmp_path / "cypher.db"
    conversations = ConversationRepository(CypherDatabase(path))
    conversation = conversations.create(title="Voice session")
    conversations.add_message(
        conversation_id=conversation["id"],
        role="user",
        content="How far away am I?",
    )
    conversations.add_message(
        conversation_id=conversation["id"],
        role="assistant",
        content="You are 42 centimeters away.",
    )

    reopened = ConversationRepository(CypherDatabase(path))
    history = reopened.history(conversation["id"])

    assert [message["role"] for message in history] == ["user", "assistant"]
    assert history[0]["content"] == "How far away am I?"


def test_conversation_history_limit_returns_latest_messages(tmp_path):
    repository = ConversationRepository(CypherDatabase(tmp_path / "cypher.db"))
    conversation = repository.create()
    for index in range(5):
        repository.add_message(conversation_id=conversation["id"], role="user", content=f"turn {index}")
    assert [item["content"] for item in repository.history(conversation["id"], limit=2)] == ["turn 3", "turn 4"]


def test_timer_survives_reopen_and_fires_once(tmp_path):
    path = tmp_path / "cypher.db"
    alarms = AlarmRepository(CypherDatabase(path))
    timer = alarms.create(
        kind="timer",
        label="One minute timer",
        trigger_at=time.time() + 60,
    )

    reopened = AlarmRepository(CypherDatabase(path))
    due = reopened.claim_due(now=timer["trigger_at"] + 1)

    assert [alarm["id"] for alarm in due] == [timer["id"]]
    assert reopened.get(timer["id"])["status"] == "fired"
    assert reopened.claim_due(now=timer["trigger_at"] + 2) == []

    completed = reopened.complete(timer["id"])
    assert completed["status"] == "completed"
