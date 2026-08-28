import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class ParsedAlarmTime:
    trigger_at: float
    local_datetime: datetime
    assumed_next_day: bool


class LocalClock:
    """Single timezone-aware clock used by conversation and scheduling tools."""

    def __init__(self, timezone: tzinfo | None = None):
        self.timezone = timezone or self._configured_timezone()

    @staticmethod
    def _configured_timezone() -> tzinfo:
        configured = os.getenv("CYPHER_TIMEZONE", "").strip()
        if configured:
            try:
                return ZoneInfo(configured)
            except ZoneInfoNotFoundError as error:
                raise RuntimeError(f"Unknown CYPHER_TIMEZONE: {configured}") from error
        return datetime.now().astimezone().tzinfo

    def now(self) -> datetime:
        return datetime.now(self.timezone)

    def timestamp(self) -> float:
        return self.now().timestamp()

    def from_timestamp(self, timestamp: float) -> datetime:
        return datetime.fromtimestamp(timestamp, self.timezone)

    def describe(self, value: datetime | None = None) -> str:
        local = (value or self.now()).astimezone(self.timezone)
        hour = local.strftime("%I").lstrip("0") or "0"
        readable = local.strftime(f"%A, %d %B %Y at {hour}:%M %p")
        return f"{readable} {self.timezone_name}"

    @property
    def timezone_name(self) -> str:
        return str(self.timezone)


class AlarmTimeParser:
    TIME_PATTERN = re.compile(
        r"\b(?P<hour>[01]?\d|2[0-3])(?:[.:](?P<minute>[0-5]\d))?\s*(?P<meridiem>a\.?m\.?|p\.?m\.?)?\b",
        re.IGNORECASE,
    )
    ISO_DATE_PATTERN = re.compile(r"\b(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b")

    def __init__(self, clock: LocalClock):
        self.clock = clock

    def parse(self, text: str) -> ParsedAlarmTime:
        now = self.clock.now()
        lower = text.lower()
        time_text = self.ISO_DATE_PATTERN.sub("", lower)
        time_match = self.TIME_PATTERN.search(time_text)
        if time_match is None:
            raise ValueError("Please include an alarm time, for example 6 AM or 18:30.")

        hour = int(time_match.group("hour"))
        minute = int(time_match.group("minute") or 0)
        meridiem = (time_match.group("meridiem") or "").replace(".", "").lower()
        if meridiem:
            if hour > 12 or hour == 0:
                raise ValueError("A 12-hour time must use an hour from 1 to 12.")
            hour = hour % 12 + (12 if meridiem == "pm" else 0)

        explicit_date = False
        if "tomorrow" in lower:
            date = (now + timedelta(days=1)).date()
            explicit_date = True
        elif "today" in lower:
            date = now.date()
            explicit_date = True
        else:
            date_match = self.ISO_DATE_PATTERN.search(lower)
            if date_match:
                try:
                    date = datetime(
                        int(date_match.group("year")),
                        int(date_match.group("month")),
                        int(date_match.group("day")),
                    ).date()
                except ValueError as error:
                    raise ValueError("That alarm date is not valid.") from error
                explicit_date = True
            else:
                date = now.date()

        candidate = datetime(
            date.year,
            date.month,
            date.day,
            hour,
            minute,
            tzinfo=self.clock.timezone,
        )
        assumed_next_day = False
        if candidate <= now:
            if explicit_date:
                raise ValueError("That alarm time is in the past.")
            candidate += timedelta(days=1)
            assumed_next_day = True

        return ParsedAlarmTime(
            trigger_at=candidate.timestamp(),
            local_datetime=candidate,
            assumed_next_day=assumed_next_day,
        )
