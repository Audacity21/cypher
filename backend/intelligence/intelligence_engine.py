from dataclasses import dataclass
from typing import Any


@dataclass
class IntelligenceDecision:
    intent: str
    reason: str
    confidence: float
    metadata: dict[str, Any] | None = None


class IntelligenceEngine:
    """
    Cypher's reasoning boundary.

    Receives semantic context and produces
    semantic intentions.

    It never communicates directly with hardware.
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

    def decide(
        self,
        event: dict,
        world_state: dict,
    ) -> IntelligenceDecision:

        event_name = event.get(
            "event",
            "UNKNOWN",
        )

        # -----------------------------------------
        # Temporary deterministic reasoning
        # -----------------------------------------
        #
        # This will eventually be replaced /
        # augmented by the local LLM.
        #
        # First we prove the intelligence contract.

        if event_name == "OBJECT_ENTERED_RANGE":
            return IntelligenceDecision(
                intent="PRESENCE",
                reason="An object entered Cypher's interaction range.",
                confidence=1.0,
            )

        if event_name == "OBJECT_LEFT_RANGE":
            return IntelligenceDecision(
                intent="IDLE",
                reason="The nearby object left Cypher's interaction range.",
                confidence=1.0,
            )

        if event_name == "LIGHTS_WENT_OFF":
            return IntelligenceDecision(
                intent="DARK",
                reason="The environment became dark.",
                confidence=1.0,
            )

        if event_name == "LIGHTS_CAME_ON":
            return IntelligenceDecision(
                intent="IDLE",
                reason="Ambient lighting returned.",
                confidence=1.0,
            )

        return IntelligenceDecision(
            intent="NONE",
            reason=(
                f"No intelligent reaction is required "
                f"for {event_name}."
            ),
            confidence=1.0,
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