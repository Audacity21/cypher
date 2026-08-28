from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from backend.agent.local_clock import AlarmTimeParser, LocalClock


class FixedClock(LocalClock):
    def __init__(self, value: datetime):
        super().__init__(value.tzinfo)
        self.value = value

    def now(self) -> datetime:
        return self.value


def clock_at(hour: int, minute: int = 0) -> FixedClock:
    return FixedClock(datetime(2030, 8, 29, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata")))


def test_six_am_uses_same_day_when_still_in_future():
    parsed = AlarmTimeParser(clock_at(5, 15)).parse("Set an alarm for 6 AM")
    assert parsed.local_datetime == datetime(2030, 8, 29, 6, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert parsed.assumed_next_day is False


def test_six_am_rolls_to_next_day_after_six():
    parsed = AlarmTimeParser(clock_at(21, 30)).parse("Wake me at 6 AM")
    assert parsed.local_datetime == datetime(2030, 8, 30, 6, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert parsed.assumed_next_day is True


def test_explicit_tomorrow_and_24_hour_time():
    parsed = AlarmTimeParser(clock_at(21, 30)).parse("Set an alarm tomorrow at 18:45")
    assert parsed.local_datetime == datetime(2030, 8, 30, 18, 45, tzinfo=ZoneInfo("Asia/Kolkata"))


def test_midnight_and_noon_are_parsed_correctly():
    midnight = AlarmTimeParser(clock_at(10)).parse("Set an alarm tomorrow at 12 AM")
    noon = AlarmTimeParser(clock_at(10)).parse("Set an alarm tomorrow at 12 PM")
    assert (midnight.local_datetime.hour, midnight.local_datetime.minute) == (0, 0)
    assert (noon.local_datetime.hour, noon.local_datetime.minute) == (12, 0)


def test_explicit_past_time_is_rejected():
    with pytest.raises(ValueError, match="in the past"):
        AlarmTimeParser(clock_at(10)).parse("Set an alarm today at 6 AM")


def test_iso_date_is_not_mistaken_for_the_time():
    parsed = AlarmTimeParser(clock_at(10)).parse("Set an alarm on 2030-08-31 at 07:20")
    assert parsed.local_datetime == datetime(2030, 8, 31, 7, 20, tzinfo=ZoneInfo("Asia/Kolkata"))


def test_clock_description_contains_local_date_time_and_zone():
    clock = clock_at(6, 5)
    assert clock.describe() == "Thursday, 29 August 2030 at 6:05 AM Asia/Kolkata"
