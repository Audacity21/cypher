from backend.intelligence.intelligence_engine import (
    IntelligenceDecision,
    IntelligenceEngine,
)


def test_deterministic_event_mapping():
    engine = IntelligenceEngine()
    expected = {
        "OBJECT_ENTERED_RANGE": "PRESENCE",
        "OBJECT_LEFT_RANGE": "IDLE",
        "LIGHTS_WENT_OFF": "DARK",
        "LIGHTS_CAME_ON": "IDLE",
        "SOMETHING_UNKNOWN": "NONE",
    }

    for event_name, expected_intent in expected.items():
        decision = engine.decide(
            event={"event": event_name, "data": {}},
            world_state={},
        )
        assert decision.intent == expected_intent
        assert engine.validate(decision) is True


def test_validation_rejects_unknown_intent_and_bad_confidence():
    engine = IntelligenceEngine()

    assert engine.validate(
        IntelligenceDecision("DESTROY", "Unsupported.", 1.0)
    ) is False
    assert engine.validate(
        IntelligenceDecision("IDLE", "Invalid range.", 2.0)
    ) is False
