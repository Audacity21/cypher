from backend.intelligence.intelligence_engine import (
    IntelligenceEngine,
)


intelligence = IntelligenceEngine()


test_events = [
    {
        "event": "OBJECT_ENTERED_RANGE",
        "data": {
            "distance_cm": 42,
        },
    },
    {
        "event": "LIGHTS_WENT_OFF",
        "data": {
            "light_percent": 1,
        },
    },
    {
        "event": "OBJECT_LEFT_RANGE",
        "data": {
            "distance_cm": 250,
        },
    },
    {
        "event": "SOMETHING_UNKNOWN",
        "data": {},
    },
]


world_state = {
    "distance_cm": 42,
    "light_percent": 1,
    "temperature_c": 27.5,
    "humidity_percent": 70,
}


for event in test_events:

    decision = intelligence.decide(
        event=event,
        world_state=world_state,
    )

    print()
    print(
        "EVENT:",
        event["event"],
    )

    print(
        "INTENT:",
        decision.intent,
    )

    print(
        "REASON:",
        decision.reason,
    )

    print(
        "CONFIDENCE:",
        decision.confidence,
    )

    print(
        "VALID:",
        intelligence.validate(
            decision
        ),
    )