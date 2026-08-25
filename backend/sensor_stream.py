import asyncio

from backend.hardware import CypherHardware


class SensorStream:
    def __init__(
        self,
        hardware: CypherHardware,
        interval: float = 0.1,
    ):
        self.hardware = hardware
        self.interval = interval

    async def distance_stream(self):
        while True:
            try:
                distance = await asyncio.to_thread(
                    self.hardware.get_distance
                )

                yield {
                    "type": "sensor",
                    "sensor": "distance",
                    "data": {
                        "distance_cm": distance,
                    },
                }

            except Exception as error:
                yield {
                    "type": "sensor_error",
                    "sensor": "distance",
                    "error": str(error),
                }

            await asyncio.sleep(self.interval)