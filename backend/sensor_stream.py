import asyncio
import time
from collections import deque

from backend.hardware import CypherHardware


class SensorStream:
    def __init__(
        self,
        hardware: CypherHardware,
        interval: float = 0.25,
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
        if light <= 50:
            return "DARK"

        if light <= 180:
            return "DIM"

        if light <= 400:
            return "NORMAL"

        return "BRIGHT"

    def _normalize_light(
        self,
        light: int,
    ) -> int:
        minimum = 12
        maximum = 520

        normalized = (
            (light - minimum)
            / (maximum - minimum)
            * 100
        )

        normalized = max(
            0,
            min(
                100,
                normalized,
            ),
        )

        return round(normalized)

    def _classify_temperature(
        self,
        temperature: float,
    ) -> str:
        if temperature < 20:
            return "COOL"

        if temperature <= 30:
            return "NORMAL"

        if temperature <= 35:
            return "WARM"

        return "HOT"

    def _classify_humidity(
        self,
        humidity: float,
    ) -> str:
        if humidity < 30:
            return "DRY"

        if humidity <= 60:
            return "NORMAL"

        if humidity <= 75:
            return "HUMID"

        return "VERY HUMID"

    async def sensor_stream(self):
        while True:
            try:
                # Keep all Arduino access sequential.
                distance = await asyncio.to_thread(
                    self.hardware.get_distance
                )

                light = await asyncio.to_thread(
                    self.hardware.get_light
                )

                climate = await asyncio.to_thread(
                    self.hardware.get_climate
                )

                temperature = climate[
                    "temperature_c"
                ]

                humidity = climate[
                    "humidity_percent"
                ]

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

                light_percent = (
                    self._normalize_light(
                        light
                    )
                )

                temperature_state = (
                    self._classify_temperature(
                        temperature
                    )
                )

                humidity_state = (
                    self._classify_humidity(
                        humidity
                    )
                )

                yield {
                    "type": "sensor_state",

                    "data": {
                        # Distance
                        "distance_cm":
                            round(
                                distance,
                                2,
                            ),

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

                        # Light
                        "light":
                            light,

                        "light_percent":
                            light_percent,

                        "light_state":
                            light_state,

                        # Climate
                        "temperature_c":
                            round(
                                temperature,
                                1,
                            ),

                        "temperature_state":
                            temperature_state,

                        "humidity_percent":
                            round(
                                humidity,
                                1,
                            ),

                        "humidity_state":
                            humidity_state,
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