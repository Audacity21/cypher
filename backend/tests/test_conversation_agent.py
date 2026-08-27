from backend.agent.conversation_agent import ConversationAgent
from backend.persistence.alarm_repository import AlarmRepository
from backend.persistence.conversation_repository import ConversationRepository
from backend.persistence.database import CypherDatabase
from backend.persistence.memory_repository import MemoryRepository


class FakeWorldState:
    def get_current_dict(self):
        return {
            "smoothed_distance_cm": 42.25,
            "light_percent": 18,
            "light_state": "DIM",
        }


class EmptyWorldState:
    def get_current_dict(self):
        return {}


class FakeLlm:
    def __init__(self):
        self.last_prompt = None

    def generate_json(self, prompt):
        self.last_prompt = prompt
        return {"reply": "Paris is the capital of France."}


class CorruptThenCorrectLlm:
    def __init__(self):
        self.calls = 0

    def generate_json(self, prompt):
        self.calls += 1
        if self.calls == 1:
            return {"reply": "My name is Ankit."}
        return {"reply": "Paris is the capital of France."}


class FakeHardware:
    def get_distance(self):
        return 55.5

    def get_light(self):
        return 100


def make_agent(tmp_path):
    database = CypherDatabase(tmp_path / "cypher.db")
    return ConversationAgent(
        conversations=ConversationRepository(database),
        memories=MemoryRepository(database),
        alarms=AlarmRepository(database),
        world_state=FakeWorldState(),
        hardware=FakeHardware(),
        llm=FakeLlm(),
    )


def test_agent_uses_live_distance_tool_and_persists_conversation(tmp_path):
    agent = make_agent(tmp_path)
    result = agent.handle(text="How far away am I?")

    assert "42.2 centimeters" in result["reply"]
    assert result["tool"]["name"] == "get_distance"
    history = agent.conversations.history(result["conversation_id"])
    assert [message["role"] for message in history] == ["user", "assistant"]


def test_agent_remembers_and_recalls_user_statement(tmp_path):
    agent = make_agent(tmp_path)
    remembered = agent.handle(text="Remember that my name is Audacity")
    recalled = agent.handle(
        text="What do you remember?",
        conversation_id=remembered["conversation_id"],
    )

    assert remembered["tool"]["name"] == "remember"
    assert "my name is Audacity" in recalled["reply"]


def test_agent_creates_persistent_timer(tmp_path):
    agent = make_agent(tmp_path)
    result = agent.handle(text="Set a timer for 30 seconds")

    assert result["tool"]["name"] == "create_timer"
    assert result["tool"]["result"]["status"] == "pending"


def test_agent_uses_qwen_for_general_question(tmp_path):
    agent = make_agent(tmp_path)
    result = agent.handle(text="What is the capital of France?")

    assert result["reply"] == "Paris is the capital of France."
    assert result["tool"] is None
    assert "assistant name is Cypher" in agent.llm.last_prompt
    assert "user's name is Ankit" in agent.llm.last_prompt


def test_qwen_prompt_contains_bounded_history_and_memory(tmp_path):
    agent = make_agent(tmp_path)
    first = agent.handle(text="Remember that I prefer concise answers")

    agent.handle(
        text="Tell me something useful",
        conversation_id=first["conversation_id"],
    )

    assert "I prefer concise answers" in agent.llm.last_prompt
    assert "Tell me something useful" in agent.llm.last_prompt


def test_corrupted_identity_reply_is_retried_with_minimal_prompt(tmp_path):
    agent = make_agent(tmp_path)
    agent.llm = CorruptThenCorrectLlm()

    result = agent.handle(text="What is the capital of France?")

    assert result["reply"] == "Paris is the capital of France."
    assert agent.llm.calls == 2


def test_distance_tool_falls_back_to_hardware_without_hud(tmp_path):
    agent = make_agent(tmp_path)
    agent.world_state = EmptyWorldState()

    result = agent.handle(text="How far away am I?")

    assert "55.5 centimeters" in result["reply"]
    assert result["tool"]["result"]["distance_cm"] == 55.5


def test_identity_roles_cannot_be_reversed_by_qwen(tmp_path):
    agent = make_agent(tmp_path)

    assistant = agent.handle(text="What is your name?")
    owner = agent.handle(text="What is my name?")

    assert assistant["reply"] == "My name is Cypher, Ankit."
    assert owner["reply"] == "Your name is Ankit."
