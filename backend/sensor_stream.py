import asyncio
import time
from collections import deque

from backend.hardware import CypherHardware


class SensorStream:
    def __init__(
        self,
        hardware: CypherHardware,
        interval: float = 0.1,
        history_size: int = 8,
    ):
        self.hardware = hardware
        self.interval = interval

        self.distance_history = deque(
            maxlen=history_size
        )

    def _analyze_motion(
        self,
        distance: float,
        timestamp: float,
    ):
        self.distance_history.append(
            (timestamp, distance)
        )

        if len(self.distance_history) < 2:
            return {
                "smoothed_distance_cm": distance,
                "velocity_cm_s": 0.0,
                "motion": "UNKNOWN",
            }

        distances = [
            item[1]
            for item in self.distance_history
        ]

        smoothed_distance = (
            sum(distances) / len(distances)
        )

        oldest_time, oldest_distance = (
            self.distance_history[0]
        )

        newest_time, newest_distance = (
            self.distance_history[-1]
        )

        delta_time = (
            newest_time - oldest_time
        )

        if delta_time <= 0:
            velocity = 0.0
        else:
            velocity = (
                newest_distance
                - oldest_distance
            ) / delta_time

        if velocity < -5:
            motion = "APPROACHING"

        elif velocity > 5:
            motion = "RECEDING"

        else:
            motion = "STATIONARY"

        return {
            "smoothed_distance_cm":
                round(smoothed_distance, 2),

            "velocity_cm_s":
                round(velocity, 2),

            "motion":
                motion,
        }

    def _classify_light(
        self,
        light: int,
    ) -> str:
        if light < 100:
            return "DARK"

        if light < 220:
            return "DIM"

        return "BRIGHT"

    async def sensor_stream(self):
        while True:
            try:
                distance = await asyncio.to_thread(
                    self.hardware.get_distance
                )

                light = await asyncio.to_thread(
                    self.hardware.get_light
                )

                timestamp = time.time()

                motion_analysis = (
                    self._analyze_motion(
                        distance,
                        timestamp,
                    )
                )

                light_state = (
                    self._classify_light(
                        light
                    )
                )

                yield {
                    "type": "sensor_state",

                    "data": {
                        "distance_cm":
                            distance,

                        "smoothed_distance_cm":
                            motion_analysis[
                                "smoothed_distance_cm"
                            ],

                        "velocity_cm_s":
                            motion_analysis[
                                "velocity_cm_s"
                            ],

                        "motion":
                            motion_analysis[
                                "motion"
                            ],

                        "light":
                            light,

                        "light_state":
                            light_state,
                    },
                }

            except Exception as error:
                yield {
                    "type": "sensor_error",
                    "error": str(error),
                }

            await asyncio.sleep(
                self.interval
            )