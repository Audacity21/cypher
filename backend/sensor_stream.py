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

        self.history = deque(
            maxlen=history_size
        )

    def _analyze_motion(
        self,
        distance: float,
        timestamp: float,
    ):
        self.history.append(
            (timestamp, distance)
        )

        if len(self.history) < 2:
            return {
                "smoothed_distance_cm": distance,
                "velocity_cm_s": 0.0,
                "motion": "UNKNOWN",
            }

        distances = [
            item[1]
            for item in self.history
        ]

        smoothed_distance = (
            sum(distances) / len(distances)
        )

        oldest_time, oldest_distance = (
            self.history[0]
        )

        newest_time, newest_distance = (
            self.history[-1]
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

    async def distance_stream(self):
        while True:
            try:
                distance = await asyncio.to_thread(
                    self.hardware.get_distance
                )

                timestamp = time.time()

                analysis = self._analyze_motion(
                    distance,
                    timestamp,
                )

                yield {
                    "type": "sensor",
                    "sensor": "distance",

                    "data": {
                        "distance_cm":
                            distance,

                        "smoothed_distance_cm":
                            analysis[
                                "smoothed_distance_cm"
                            ],

                        "velocity_cm_s":
                            analysis[
                                "velocity_cm_s"
                            ],

                        "motion":
                            analysis["motion"],
                    },
                }

            except Exception as error:
                yield {
                    "type": "sensor_error",
                    "sensor": "distance",
                    "error": str(error),
                }

            await asyncio.sleep(
                self.interval
            )