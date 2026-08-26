import time

from backend.perception.world_state import WorldState


class EventEngine:
    def __init__(self):
        self.last_event_times: dict[str, float] = {}

        self.cooldowns = {
            "LIGHTS_WENT_OFF": 3.0,
            "LIGHTS_CAME_ON": 3.0,

            "OBJECT_STARTED_APPROACHING": 3.0,
            "OBJECT_STARTED_RECEDING": 3.0,

            "OBJECT_ENTERED_RANGE": 3.0,
            "OBJECT_LEFT_RANGE": 3.0,
        }

        self.object_range_cm = 100.0
        self.max_tracking_distance_cm = 200.0

        # Require a motion state to persist before emitting.
        self.motion_candidate: str | None = None
        self.motion_candidate_count = 0
        self.motion_confirmation_samples = 2

    def _can_emit(
        self,
        event_type: str,
    ) -> bool:
        now = time.time()

        last_time = self.last_event_times.get(
            event_type,
            0.0,
        )

        cooldown = self.cooldowns.get(
            event_type,
            0.0,
        )

        if now - last_time < cooldown:
            return False

        self.last_event_times[event_type] = now

        return True

    def _create_event(
        self,
        event_type: str,
        data: dict | None = None,
    ) -> dict:
        return {
            "type": "event",
            "event": event_type,
            "timestamp": time.time(),
            "data": data or {},
        }

    def _confirm_motion(
        self,
        motion: str,
    ) -> bool:
        if motion not in (
            "APPROACHING",
            "RECEDING",
        ):
            self.motion_candidate = None
            self.motion_candidate_count = 0
            return False

        if self.motion_candidate == motion:
            self.motion_candidate_count += 1
        else:
            self.motion_candidate = motion
            self.motion_candidate_count = 1

        if (
            self.motion_candidate_count
            >= self.motion_confirmation_samples
        ):
            self.motion_candidate = None
            self.motion_candidate_count = 0
            return True

        return False

    def evaluate(
        self,
        previous: WorldState,
        current: WorldState,
    ) -> list[dict]:
        events = []

        if previous.updated_at == 0:
            return events

        # =====================================================
        # LIGHT EVENTS
        # =====================================================

        if (
            previous.light_state != "DARK"
            and current.light_state == "DARK"
        ):
            if self._can_emit(
                "LIGHTS_WENT_OFF"
            ):
                events.append(
                    self._create_event(
                        "LIGHTS_WENT_OFF",
                        {
                            "previous":
                                previous.light_state,

                            "current":
                                current.light_state,

                            "light_percent":
                                current.light_percent,
                        },
                    )
                )

        if (
            previous.light_state == "DARK"
            and current.light_state != "DARK"
        ):
            if self._can_emit(
                "LIGHTS_CAME_ON"
            ):
                events.append(
                    self._create_event(
                        "LIGHTS_CAME_ON",
                        {
                            "previous":
                                previous.light_state,

                            "current":
                                current.light_state,

                            "light_percent":
                                current.light_percent,
                        },
                    )
                )

        # =====================================================
        # MOTION EVENTS
        # =====================================================

        current_distance = (
            current.smoothed_distance_cm
        )

        # Never generate motion events outside trusted range.
        if (
            current_distance is not None
            and 0
            < current_distance
            <= self.max_tracking_distance_cm
        ):
            if self._confirm_motion(
                current.motion
            ):
                if (
                    current.motion
                    == "APPROACHING"
                    and self._can_emit(
                        "OBJECT_STARTED_APPROACHING"
                    )
                ):
                    events.append(
                        self._create_event(
                            "OBJECT_STARTED_APPROACHING",
                            {
                                "distance_cm":
                                    current_distance,

                                "velocity_cm_s":
                                    current.velocity_cm_s,
                            },
                        )
                    )

                elif (
                    current.motion
                    == "RECEDING"
                    and self._can_emit(
                        "OBJECT_STARTED_RECEDING"
                    )
                ):
                    events.append(
                        self._create_event(
                            "OBJECT_STARTED_RECEDING",
                            {
                                "distance_cm":
                                    current_distance,

                                "velocity_cm_s":
                                    current.velocity_cm_s,
                            },
                        )
                    )
        else:
            self.motion_candidate = None
            self.motion_candidate_count = 0

        # =====================================================
        # RANGE EVENTS
        # =====================================================

        previous_distance = (
            previous.smoothed_distance_cm
        )

        current_distance = (
            current.smoothed_distance_cm
        )

        if (
            previous_distance is not None
            and current_distance is not None
        ):
            # Only compare valid ultrasonic readings.
            previous_valid = (
                0
                < previous_distance
                <= self.max_tracking_distance_cm
            )

            current_valid = (
                0
                < current_distance
                <= self.max_tracking_distance_cm
            )

            previously_inside = (
                previous_valid
                and previous_distance
                <= self.object_range_cm
            )

            currently_inside = (
                current_valid
                and current_distance
                <= self.object_range_cm
            )

            if (
                not previously_inside
                and currently_inside
            ):
                if self._can_emit(
                    "OBJECT_ENTERED_RANGE"
                ):
                    events.append(
                        self._create_event(
                            "OBJECT_ENTERED_RANGE",
                            {
                                "distance_cm":
                                    current_distance,
                            },
                        )
                    )

            if (
                previously_inside
                and not currently_inside
            ):
                if self._can_emit(
                    "OBJECT_LEFT_RANGE"
                ):
                    events.append(
                        self._create_event(
                            "OBJECT_LEFT_RANGE",
                            {
                                "distance_cm":
                                    current_distance,
                            },
                        )
                    )

        return events