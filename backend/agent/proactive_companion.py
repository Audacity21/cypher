import re
import time
from collections import deque


class ProactiveCompanion:
    """Runs Cypher's inactivity-based room identity challenge."""

    TRIGGER_EVENTS = {"OBJECT_ENTERED_RANGE", "LIGHTS_CAME_ON"}

    def __init__(self, inactivity_seconds: float = 600, response_seconds: float = 10, clock=time.time):
        self.inactivity_seconds = inactivity_seconds
        self.response_seconds = response_seconds
        self.clock = clock
        self.last_interaction_at = clock()
        self.challenge_deadline: float | None = None
        self.notifications: deque[dict] = deque(maxlen=20)

    def record_interaction(self) -> None:
        self.last_interaction_at = self.clock()

    def handle_event(self, event: dict) -> dict | None:
        event_type = event.get("event")
        timestamp = float(event.get("timestamp", self.clock()))
        if (
            event_type not in self.TRIGGER_EVENTS
            or self.challenge_deadline is not None
            or timestamp - self.last_interaction_at < self.inactivity_seconds
        ):
            return None
        self.challenge_deadline = timestamp + self.response_seconds
        notification = {
            "type": "IDENTITY_CHALLENGE",
            "text": "Hi, who's this?",
            "timestamp": timestamp,
        }
        self.notifications.append(notification)
        return notification

    def respond(self, text: str) -> str | None:
        if self.challenge_deadline is None:
            return None
        if re.search(r"\bankit\b", text, re.IGNORECASE):
            self.challenge_deadline = None
            self.record_interaction()
            return "verified"
        return "awaiting"

    def check_timeout(self) -> bool:
        if self.challenge_deadline is None or self.clock() < self.challenge_deadline:
            return False
        self.challenge_deadline = None
        return True

    def drain(self, limit: int | None = None) -> list[dict]:
        count = len(self.notifications) if limit is None else min(limit, len(self.notifications))
        return [self.notifications.popleft() for _ in range(count)]
