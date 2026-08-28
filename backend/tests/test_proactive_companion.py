from backend.agent.proactive_companion import ProactiveCompanion


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def event(name, timestamp):
    return {"event": name, "timestamp": timestamp}


def test_person_challenge_after_ten_minutes_and_identity_cancels_alarm():
    clock = Clock()
    companion = ProactiveCompanion(inactivity_seconds=600, response_seconds=10, clock=clock)
    clock.now = 701
    result = companion.handle_event(event("OBJECT_ENTERED_RANGE", clock.now))
    assert result["type"] == "IDENTITY_CHALLENGE"
    assert "Ankit" not in result["text"]
    clock.now = 705
    assert companion.respond("It is Ankit") == "verified"
    clock.now = 720
    assert companion.check_timeout() is False


def test_lights_on_challenge_buzzes_after_ten_seconds_without_keyword():
    clock = Clock()
    companion = ProactiveCompanion(inactivity_seconds=600, response_seconds=10, clock=clock)
    clock.now = 701
    companion.handle_event(event("LIGHTS_CAME_ON", clock.now))
    assert companion.respond("hello") == "awaiting"
    clock.now = 712
    assert companion.check_timeout() is True
    assert companion.check_timeout() is False


def test_no_challenge_during_recent_conversation():
    clock = Clock()
    companion = ProactiveCompanion(inactivity_seconds=600, clock=clock)
    clock.now = 500
    assert companion.handle_event(event("OBJECT_ENTERED_RANGE", clock.now)) is None
