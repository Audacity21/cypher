from backend.actions.action_engine import ActionEngine


class FakeHardware:
    def __init__(self):
        self.tones = []
        self.stopped = False

    def play_tone(self, frequency_hz, duration_ms):
        tone = {
            "frequency_hz": frequency_hz,
            "duration_ms": duration_ms,
        }
        self.tones.append(tone)
        return tone

    def stop_buzzer(self):
        self.stopped = True
        return {}


def test_alert_sound_uses_semantic_pattern(monkeypatch):
    hardware = FakeHardware()
    actions = ActionEngine(hardware)
    monkeypatch.setattr("backend.actions.action_engine.time.sleep", lambda _: None)

    result = actions.play_sound("ALERT")

    assert result["sound"] == "ALERT"
    assert [tone["frequency_hz"] for tone in hardware.tones] == [440, 660, 440]


def test_stop_sound_reaches_hardware():
    hardware = FakeHardware()
    actions = ActionEngine(hardware)

    actions.stop_sound()

    assert hardware.stopped is True
