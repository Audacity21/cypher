from dataclasses import asdict, dataclass
from time import time


@dataclass
class WorldState:
    # -------------------------
    # Spatial perception
    # -------------------------

    distance_cm: float | None = None
    smoothed_distance_cm: float | None = None
    velocity_cm_s: float = 0.0
    motion: str = "UNKNOWN"
    tracking: bool = False

    # -------------------------
    # Light perception
    # -------------------------

    light_raw: int | None = None
    light_percent: int | None = None
    light_state: str = "UNKNOWN"

    # -------------------------
    # Climate perception
    # -------------------------

    temperature_c: float | None = None
    temperature_state: str = "UNKNOWN"

    humidity_percent: float | None = None
    humidity_state: str = "UNKNOWN"

    # -------------------------
    # Metadata
    # -------------------------

    updated_at: float = 0.0

    def update(
        self,
        sensor_data: dict,
    ) -> None:
        """
        Update the world state using processed
        sensor data from SensorStream.
        """

        self.distance_cm = sensor_data.get(
            "distance_cm",
            self.distance_cm,
        )

        self.smoothed_distance_cm = sensor_data.get(
            "smoothed_distance_cm",
            self.smoothed_distance_cm,
        )

        self.velocity_cm_s = sensor_data.get(
            "velocity_cm_s",
            self.velocity_cm_s,
        )

        self.motion = sensor_data.get(
            "motion",
            self.motion,
        )

        self.light_raw = sensor_data.get(
            "light",
            self.light_raw,
        )

        self.light_percent = sensor_data.get(
            "light_percent",
            self.light_percent,
        )

        self.light_state = sensor_data.get(
            "light_state",
            self.light_state,
        )

        self.temperature_c = sensor_data.get(
            "temperature_c",
            self.temperature_c,
        )

        self.temperature_state = sensor_data.get(
            "temperature_state",
            self.temperature_state,
        )

        self.tracking = sensor_data.get(
            "tracking",
            self.tracking,
        )

        self.humidity_percent = sensor_data.get(
            "humidity_percent",
            self.humidity_percent,
        )

        self.humidity_state = sensor_data.get(
            "humidity_state",
            self.humidity_state,
        )

        self.updated_at = time()

    def to_dict(self) -> dict:
        return asdict(self)