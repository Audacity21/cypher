from datetime import datetime
from zoneinfo import ZoneInfo

from backend.agent.local_clock import LocalClock
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
            "temperature_c": 27.0,
            "temperature_state": "NORMAL",
            "humidity_percent": 63.0,
            "humidity_state": "HUMID",
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

    def get_climate(self):
        return {"temperature_c": 27.0, "humidity_percent": 63.0}


class FakeActions:
    def __init__(self):
        self.status = "OFF"

    def set_status(self, status):
        self.status = status
        return {"status": status, "rgb": {}}

    def play_sound(self, sound):
        return {"sound": sound, "tones": []}

    def stop_sound(self):
        return {"stopped": True}

    def get_status(self):
        return self.status


class FakeMusicResolver:
    def __init__(self):
        self.stopped = False

    def play(self, query=None):
        return {
            "video_id": "dX3k_QDnzHE" if query else "e8WoWk4b3D0",
            "title": query or "Levitating",
            "watch_url": "https://music.youtube.com/watch?v=dX3k_QDnzHE" if query else "https://music.youtube.com/watch?v=e8WoWk4b3D0",
            "playlist_id": None if query else "PLRHSp1QuRiOY",
        }

    def stop(self):
        self.stopped = True
        return {"stopped": True}


class FixedClock(LocalClock):
    def __init__(self):
        super().__init__(ZoneInfo("Asia/Kolkata"))

    def now(self):
        return datetime(2030, 8, 29, 21, 30, tzinfo=self.timezone)


def make_agent(tmp_path, *, clock=None):
    database = CypherDatabase(tmp_path / "cypher.db")
    return ConversationAgent(
        conversations=ConversationRepository(database),
        memories=MemoryRepository(database),
        alarms=AlarmRepository(database),
        world_state=FakeWorldState(),
        hardware=FakeHardware(),
        actions=FakeActions(),
        llm=FakeLlm(),
        music_resolver=FakeMusicResolver(),
        clock=clock,
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


def test_agent_reports_injected_local_date_and_time(tmp_path):
    agent = make_agent(tmp_path, clock=FixedClock())
    result = agent.handle(text="What time is it?")
    assert result["reply"] == "It is Thursday, 29 August 2030 at 9:30 PM Asia/Kolkata, Ankit."
    assert result["tool"]["result"]["timezone"] == "Asia/Kolkata"


def test_agent_sets_six_am_alarm_for_next_local_day(tmp_path):
    agent = make_agent(tmp_path, clock=FixedClock())
    result = agent.handle(text="Set an alarm for 6 AM")
    alarm = result["tool"]["result"]
    assert result["tool"]["name"] == "create_alarm"
    assert alarm["kind"] == "alarm"
    assert alarm["scheduled_for"] == "Friday, 30 August 2030 at 6:00 AM Asia/Kolkata"
    assert alarm["assumed_next_day"] is True
    assert datetime.fromtimestamp(alarm["trigger_at"], ZoneInfo("Asia/Kolkata")) == datetime(
        2030, 8, 30, 6, 0, tzinfo=ZoneInfo("Asia/Kolkata")
    )


def test_agent_lists_alarm_with_local_time(tmp_path):
    agent = make_agent(tmp_path, clock=FixedClock())
    created = agent.handle(text="Wake me at 6 AM")
    listed = agent.handle(text="List my alarms", conversation_id=created["conversation_id"])
    assert listed["tool"]["name"] == "list_alarms"
    assert listed["tool"]["result"][0]["local_time"].endswith("6:00 AM Asia/Kolkata")


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


def test_greeting_always_addresses_ankit(tmp_path):
    agent = make_agent(tmp_path)
    assert agent.handle(text="Hello Cypher")["reply"] == "Hello, Ankit. Cypher is listening."


def test_agent_can_run_allowlisted_rgb_action(tmp_path):
    agent = make_agent(tmp_path)

    result = agent.handle(text="Cypher, set the lights to purple")

    assert result["tool"]["name"] == "set_cypher_status"
    assert result["tool"]["result"]["status"] == "THINKING"
    assert agent.actions.status == "THINKING"


def test_agent_can_run_allowlisted_sound_action(tmp_path):
    agent = make_agent(tmp_path)

    result = agent.handle(text="Run a sound check")

    assert result["tool"]["name"] == "play_cypher_sound"
    assert result["tool"]["result"]["sound"] == "PRESENCE"


def test_agent_can_stop_buzzer(tmp_path):
    agent = make_agent(tmp_path)
    result = agent.handle(text="Silence the buzzer")
    assert result["tool"]["name"] == "stop_cypher_sound"


def test_agent_can_start_default_music_playlist(tmp_path):
    agent = make_agent(tmp_path)
    result = agent.handle(text="Play my playlist")
    assert result["tool"] == {
        "name": "play_music",
        "result": {
            "video_id": "e8WoWk4b3D0",
            "title": "Levitating",
            "watch_url": "https://music.youtube.com/watch?v=e8WoWk4b3D0",
            "playlist_id": "PLRHSp1QuRiOY",
        },
    }


def test_agent_can_request_a_song(tmp_path):
    agent = make_agent(tmp_path)
    result = agent.handle(text="Play Midnight City on YouTube Music")
    assert result["tool"]["name"] == "play_music"
    assert result["tool"]["result"]["video_id"] == "dX3k_QDnzHE"


def test_agent_can_stop_music(tmp_path):
    agent = make_agent(tmp_path)
    result = agent.handle(text="Stop the music")
    assert result["tool"] == {"name": "stop_music", "result": {"stopped": True}}


def test_agent_reports_real_system_status(tmp_path):
    agent = make_agent(tmp_path)
    result = agent.handle(text="Give me a system status report")
    assert result["tool"]["name"] == "get_system_status"
    assert result["tool"]["result"]["distance_cm"] == 42.25
    assert "hardware state is off" in result["reply"]


def test_temperature_never_falls_through_to_qwen(tmp_path):
    agent = make_agent(tmp_path)
    result = agent.handle(text="What is the temperature?")
    assert result["tool"]["name"] == "get_temperature"
    assert result["tool"]["result"]["temperature_c"] == 27.0

    short_prompt = agent.handle(text="Room temp?")
    assert short_prompt["tool"]["name"] == "get_temperature"


def test_agent_can_set_yellow_light(tmp_path):
    agent = make_agent(tmp_path)
    result = agent.handle(text="Turn the light yellow")
    assert result["tool"]["result"]["status"] == "YELLOW"
