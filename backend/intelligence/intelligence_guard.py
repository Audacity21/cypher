from dataclasses import dataclass

from backend.intelligence.intelligence_engine import IntelligenceDecision


@dataclass
class GuardResult:
    allowed: bool
    reason: str


class IntelligenceGuard:
    """
    Final safety gate between an LLM decision
    and any downstream Cypher behavior.
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

    def __init__(
        self,
        minimum_confidence: float = 0.70,
    ):
        self.minimum_confidence = (
            minimum_confidence
        )

    def evaluate(
        self,
        decision: IntelligenceDecision,
    ) -> GuardResult:

        # -----------------------------------------
        # Intent
        # -----------------------------------------

        if (
            decision.intent
            not in self.ALLOWED_INTENTS
        ):
            return GuardResult(
                allowed=False,
                reason="unknown_intent",
            )

        # -----------------------------------------
        # Confidence type
        # -----------------------------------------

        if not isinstance(
            decision.confidence,
            (int, float),
        ):
            return GuardResult(
                allowed=False,
                reason="invalid_confidence_type",
            )

        # -----------------------------------------
        # Confidence range
        # -----------------------------------------

        if not (
            0.0
            <= decision.confidence
            <= 1.0
        ):
            return GuardResult(
                allowed=False,
                reason="confidence_out_of_range",
            )

        # -----------------------------------------
        # Confidence threshold
        # -----------------------------------------

        if (
            decision.confidence
            < self.minimum_confidence
        ):
            return GuardResult(
                allowed=False,
                reason="confidence_below_threshold",
            )

        # -----------------------------------------
        # Reason
        # -----------------------------------------

        if (
            not decision.reason
            or not isinstance(
                decision.reason,
                str,
            )
        ):
            return GuardResult(
                allowed=False,
                reason="missing_reason",
            )

        return GuardResult(
            allowed=True,
            reason="accepted",
        )