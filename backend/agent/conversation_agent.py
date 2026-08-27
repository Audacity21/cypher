import re
import time

from backend.intelligence.llm_provider import OllamaProvider
from backend.persistence.alarm_repository import AlarmRepository
from backend.persistence.conversation_repository import ConversationRepository
from backend.persistence.memory_repository import MemoryRepository


class ConversationAgent:
    TIMER_PATTERN = re.compile(
        r"(?:timer|remind me)(?:\s+for|\s+in)?\s+"
        r"(?P<amount>\d+(?:\.\d+)?)\s*"
        r"(?P<unit>seconds?|minutes?|hours?)",
        re.IGNORECASE,
    )

    def __init__(
        self,
        *,
        conversations: ConversationRepository,
        memories: MemoryRepository,
        alarms: AlarmRepository,
        world_state,
        hardware,
        llm: OllamaProvider,
    ):
        self.conversations = conversations
        self.memories = memories
        self.alarms = alarms
        self.world_state = world_state
        self.hardware = hardware
        self.llm = llm

    def handle(self, *, text: str, conversation_id: str | None = None) -> dict:
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("message cannot be empty")

        if conversation_id is None:
            conversation = self.conversations.create(title="Cypher session")
            conversation_id = conversation["id"]
        elif self.conversations.get(conversation_id) is None:
            raise ValueError("conversation not found")

        self.conversations.add_message(
            conversation_id=conversation_id,
            role="user",
            content=clean_text,
        )

        reply, tool = self._respond(clean_text)

        self.conversations.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=reply,
        )
        return {
            "conversation_id": conversation_id,
            "reply": reply,
            "tool": tool,
        }

    def _respond(self, text: str) -> tuple[str, dict | None]:
        lower = text.lower()
        timer_match = self.TIMER_PATTERN.search(text)
        if timer_match:
            amount = float(timer_match.group("amount"))
            unit = timer_match.group("unit").lower()
            multiplier = 1 if unit.startswith("second") else 60
            if unit.startswith("hour"):
                multiplier = 3600
            seconds = amount * multiplier
            if not 0 < seconds <= 86400:
                return "I can set timers up to 24 hours.", None

            alarm = self.alarms.create(
                kind="timer",
                label=text,
                trigger_at=time.time() + seconds,
            )
            return (
                f"Timer set for {amount:g} {unit}.",
                {"name": "create_timer", "result": alarm},
            )

        if "how far" in lower or "distance" in lower:
            state = self.world_state.get_current_dict()
            distance = state.get("smoothed_distance_cm")
            if distance is None:
                distance = self.hardware.get_distance()
            return (
                f"The current distance is {float(distance):.1f} centimeters.",
                {"name": "get_distance", "result": {"distance_cm": distance}},
            )

        if "light level" in lower or "how bright" in lower:
            state = self.world_state.get_current_dict()
            percent = state.get("light_percent")
            light_state = state.get("light_state", "UNKNOWN")
            if percent is None:
                raw = self.hardware.get_light()
                percent = round(max(0, min(100, (raw - 12) / (520 - 12) * 100)))
                light_state = (
                    "DARK" if raw <= 50
                    else "DIM" if raw <= 180
                    else "NORMAL" if raw <= 400
                    else "BRIGHT"
                )
            return (
                f"Ambient light is {percent} percent, classified as {light_state}.",
                {
                    "name": "get_light_level",
                    "result": {"light_percent": percent, "light_state": light_state},
                },
            )

        if lower.startswith("remember that "):
            content = text[len("remember that "):].strip()
            memory = self.memories.remember(
                content=content,
                category="user_statement",
                importance=0.8,
                source="conversation",
            )
            return (
                "I will remember that.",
                {"name": "remember", "result": memory},
            )

        if "what do you remember" in lower:
            memories = self.memories.recall(limit=5)
            if not memories:
                return "I do not have any saved memories yet.", None
            summary = "; ".join(memory["content"] for memory in memories)
            return (
                f"I remember: {summary}",
                {"name": "recall", "result": memories},
            )

        result = self.llm.generate_json(
            f"""
You are Cypher, a concise local desktop companion.
Answer the user's general-knowledge question in one or two short sentences.
Do not claim to use tools or sensors. Return JSON only.

USER:
{text}

Return exactly:
{{"reply": "<answer>"}}
"""
        )
        reply = result.get("reply")
        if not isinstance(reply, str) or not reply.strip():
            raise RuntimeError("Qwen returned an invalid reply")
        return reply.strip(), None
