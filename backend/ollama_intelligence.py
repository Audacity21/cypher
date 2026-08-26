from backend.intelligence_engine import IntelligenceDecision
from backend.llm_provider import OllamaProvider


class OllamaIntelligence:
    """
    LLM-backed Cypher intelligence.

    SHADOW MODE:
    Decisions produced here are observed and logged,
    but are NOT allowed to control hardware yet.
    """

    ALLOWED_INTENTS = {
        "NONE",
        "IDLE",
        "PRESENCE",
        "DARK",
        "ALERT",
        "SUCCESS",
        "THINKING",
    }

    def __init__(self):
        self.llm = OllamaProvider(
            model="qwen2.5:1.5b"
        )

    def decide(
        self,
        event: dict,
        world_state: dict,
    ) -> IntelligenceDecision:

        event_name = event.get(
            "event",
            "UNKNOWN",
        )

        event_data = event.get(
            "data",
            {},
        )

        prompt = f"""
You are the reasoning engine inside Cypher,
a local physical AI companion.

Your job is NOT to decide whether something is dangerous.

Your job is to choose the semantic state that best represents
how Cypher should respond to the event.

You MUST choose exactly one allowed intent.

============================================================
INTENTS
============================================================

PRESENCE
Use when something enters Cypher's nearby interaction range.
This does NOT mean danger.
It means Cypher acknowledges that something is nearby.

IDLE
Use when Cypher should return to its normal resting state.
Examples:
- an object leaves interaction range
- lighting returns after darkness

DARK
Use when the environment transitions into darkness.

ALERT
Use only when an event genuinely requires attention or warning.

SUCCESS
Use when an operation successfully completes.

THINKING
Use when Cypher is actively processing a request.

NONE
Use only when the event does not justify ANY change
in Cypher's semantic state.

============================================================
IMPORTANT EVENT INTERPRETATION
============================================================

OBJECT_ENTERED_RANGE
normally means PRESENCE.

OBJECT_LEFT_RANGE
normally means IDLE.

LIGHTS_WENT_OFF
normally means DARK.

LIGHTS_CAME_ON
normally means IDLE.

OBJECT_STARTED_APPROACHING
usually means NONE unless other context makes it important.

OBJECT_STARTED_RECEDING
usually means NONE unless other context makes it important.

These are semantic states, not danger classifications.

============================================================
RULES
============================================================

- Only choose from the allowed intents.
- Never control hardware directly.
- Do not invent facts.
- Use both the event and world state.
- Keep the reason to one short sentence.
- confidence must be from 0 to 1.
- Return JSON only.

============================================================
CURRENT EVENT
============================================================

Event:
{event_name}

Event data:
{event_data}

============================================================
CURRENT WORLD STATE
============================================================

{world_state}

============================================================
OUTPUT
============================================================

Return exactly:

{{
  "intent": "<intent>",
  "reason": "<one short sentence>",
  "confidence": <number between 0 and 1>
}}
"""

        result = self.llm.generate_json(
            prompt
        )

        intent = str(
            result.get(
                "intent",
                "NONE",
            )
        ).upper()

        reason = str(
            result.get(
                "reason",
                "No reason provided.",
            )
        )

        try:
            confidence = float(
                result.get(
                    "confidence",
                    0.0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            confidence = 0.0

        return IntelligenceDecision(
            intent=intent,
            reason=reason,
            confidence=confidence,
            metadata={
                "provider": "ollama",
                "model": "qwen2.5:1.5b",
                "mode": "shadow",
            },
        )

    def validate(
        self,
        decision: IntelligenceDecision,
    ) -> bool:

        if (
            decision.intent
            not in self.ALLOWED_INTENTS
        ):
            return False

        if not (
            0.0
            <= decision.confidence
            <= 1.0
        ):
            return False

        return True