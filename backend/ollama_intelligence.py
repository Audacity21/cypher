from backend.intelligence_engine import (
    IntelligenceDecision,
)

from backend.llm_provider import (
    OllamaProvider,
)


class OllamaIntelligence:
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

Choose exactly ONE semantic intent.

INTENTS:

PRESENCE
Something entered Cypher's nearby interaction range.

IDLE
Return to Cypher's normal resting state.

DARK
The environment transitioned into darkness.

ALERT
Something genuinely requires attention.

SUCCESS
An operation completed successfully.

THINKING
Cypher is actively processing a request.

NONE
No semantic state change is appropriate.

IMPORTANT INTERPRETATION:

OBJECT_ENTERED_RANGE -> normally PRESENCE
OBJECT_LEFT_RANGE -> normally IDLE
LIGHTS_WENT_OFF -> normally DARK
LIGHTS_CAME_ON -> normally IDLE

OBJECT_STARTED_APPROACHING ->
usually NONE unless context makes it important.

OBJECT_STARTED_RECEDING ->
usually NONE unless context makes it important.

RULES:

- Choose only an allowed intent.
- Never invent sensor information.
- Never describe or request Arduino pins.
- Never issue hardware commands.
- confidence must be between 0 and 1.
- reason must be one short sentence.
- Return JSON only.

EVENT:
{event_name}

EVENT DATA:
{event_data}

WORLD STATE:
{world_state}

Return exactly:

{{
  "intent": "<intent>",
  "reason": "<short reason>",
  "confidence": <number>
}}
"""

        result = self.llm.generate_json(
            prompt
        )

        required_fields = {
            "intent",
            "reason",
            "confidence",
        }

        missing = (
            required_fields
            - result.keys()
        )

        if missing:
            raise ValueError(
                f"Missing LLM fields: "
                f"{sorted(missing)}"
            )

        intent = result["intent"]

        reason = result["reason"]

        confidence = result[
            "confidence"
        ]

        if not isinstance(
            intent,
            str,
        ):
            raise ValueError(
                "LLM intent must be a string"
            )

        if not isinstance(
            reason,
            str,
        ):
            raise ValueError(
                "LLM reason must be a string"
            )

        if not isinstance(
            confidence,
            (int, float),
        ):
            raise ValueError(
                "LLM confidence must be numeric"
            )

        return IntelligenceDecision(
            intent=intent.upper(),
            reason=reason,
            confidence=float(
                confidence
            ),
            metadata={
                "provider": "ollama",
                "model":
                    "qwen2.5:1.5b",
                "mode":
                    "shadow",
            },
        )