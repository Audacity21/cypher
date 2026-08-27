from backend.intelligence.intelligence_engine import IntelligenceDecision
from backend.intelligence.intelligence_guard import IntelligenceGuard


def test_guard_accepts_valid_decision():
    result = IntelligenceGuard().evaluate(
        IntelligenceDecision("PRESENCE", "Valid decision.", 0.95)
    )

    assert result.allowed is True
    assert result.reason == "accepted"


def test_guard_rejects_each_invalid_boundary():
    guard = IntelligenceGuard(minimum_confidence=0.70)
    cases = [
        (
            IntelligenceDecision("DELETE_SYSTEM", "Bad intent.", 1.0),
            "unknown_intent",
        ),
        (
            IntelligenceDecision("ALERT", "Low confidence.", 0.2),
            "confidence_below_threshold",
        ),
        (
            IntelligenceDecision("DARK", "Invalid confidence.", 5.0),
            "confidence_out_of_range",
        ),
        (IntelligenceDecision("IDLE", "", 0.9), "missing_reason"),
    ]

    for decision, expected_reason in cases:
        result = guard.evaluate(decision)
        assert result.allowed is False
        assert result.reason == expected_reason
