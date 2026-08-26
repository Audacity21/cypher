from backend.hardware.serial_manager import SerialManager


class CypherHardware:
    def __init__(
        self,
        port: str,
    ):
        self.serial = SerialManager(
            port=port
        )

    def connect(self):
        self.serial.connect()

    def disconnect(self):
        self.serial.disconnect()

    # =========================================================
    # SENSORS
    # =========================================================

    def get_distance(
        self,
    ) -> float:
        response = (
            self.serial.send_command(
                "GET_DISTANCE"
            )
        )

        if not response.get("ok"):
            raise RuntimeError(
                response.get(
                    "error",
                    "Unknown distance sensor error",
                )
            )

        return float(
            response["data"][
                "distance_cm"
            ]
        )

    def get_light(
        self,
    ) -> int:
        response = (
            self.serial.send_command(
                "GET_LIGHT"
            )
        )

        if not response.get("ok"):
            raise RuntimeError(
                response.get(
                    "error",
                    "Unknown light sensor error",
                )
            )

        return int(
            response["data"][
                "light"
            ]
        )

    def get_climate(
        self,
    ) -> dict:
        response = (
            self.serial.send_command(
                "GET_CLIMATE"
            )
        )

        if not response.get("ok"):
            raise RuntimeError(
                response.get(
                    "error",
                    "Unknown climate sensor error",
                )
            )

        return {
            "temperature_c": float(
                response["data"][
                    "temperature_c"
                ]
            ),

            "humidity_percent": float(
                response["data"][
                    "humidity_percent"
                ]
            ),
        }

    # =========================================================
    # ACTIONS
    # =========================================================

    def set_rgb(
        self,
        red: int,
        green: int,
        blue: int,
    ) -> dict:
        for value in (
            red,
            green,
            blue,
        ):
            if not isinstance(
                value,
                int,
            ):
                raise TypeError(
                    "RGB values must be integers"
                )

            if not 0 <= value <= 255:
                raise ValueError(
                    "RGB values must be between 0 and 255"
                )

        response = (
            self.serial.send_command(
                "SET_RGB",
                {
                    "r": red,
                    "g": green,
                    "b": blue,
                },
            )
        )

        if not response.get("ok"):
            raise RuntimeError(
                response.get(
                    "error",
                    "Unknown RGB action error",
                )
            )

        return response["data"]

    def rgb_off(
        self,
    ) -> dict:
        return self.set_rgb(
            0,
            0,
            0,
        )