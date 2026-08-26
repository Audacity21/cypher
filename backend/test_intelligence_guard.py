from backend.intelligence_engine import (
    IntelligenceDecision,
)

from backend.intelligence_guard import (
    IntelligenceGuard,
)


guard = IntelligenceGuard(
    minimum_confidence=0.70
)


tests = [
    IntelligenceDecision(
        intent="PRESENCE",
        reason="Valid decision.",
        confidence=0.95,
    ),

    IntelligenceDecision(
        intent="DELETE_SYSTEM",
        reason="Bad intent.",
        confidence=1.0,
    ),

    IntelligenceDecision(
        intent="ALERT",
        reason="Low confidence.",
        confidence=0.2,
    ),

    IntelligenceDecision(
        intent="DARK",
        reason="Invalid confidence.",
        confidence=5.0,
    ),

    IntelligenceDecision(
        intent="IDLE",
        reason="",
        confidence=0.9,
    ),
]


for decision in tests:

    result = guard.evaluate(
        decision
    )

    print()
    print(
        "INTENT:",
        decision.intent
    )

    print(
        "CONFIDENCE:",
        decision.confidence
    )

    print(
        "ALLOWED:",
        result.allowed
    )

    print(
        "REASON:",
        result.reason
    )