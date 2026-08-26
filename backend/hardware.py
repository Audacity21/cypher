from backend.serial_manager import SerialManager


class CypherHardware:
    def __init__(self, port: str):
        self.serial = SerialManager(port=port)

    def connect(self):
        self.serial.connect()

    def disconnect(self):
        self.serial.disconnect()

    def get_distance(self) -> float:
        response = self.serial.send_command("GET_DISTANCE")

        if not response.get("ok"):
            raise RuntimeError(
                response.get(
                    "error",
                    "Unknown distance sensor error",
                )
            )

        return float(
            response["data"]["distance_cm"]
        )

    def get_light(self) -> int:
        response = self.serial.send_command("GET_LIGHT")

        if not response.get("ok"):
            raise RuntimeError(
                response.get(
                    "error",
                    "Unknown light sensor error",
                )
            )

        return int(
            response["data"]["light"]
        )

    def get_climate(self) -> dict:
        response = self.serial.send_command("GET_CLIMATE")

        if not response.get("ok"):
            raise RuntimeError(
                response.get(
                    "error",
                    "Unknown climate sensor error",
                )
            )

        return {
            "temperature_c": float(
                response["data"]["temperature_c"]
            ),
            "humidity_percent": float(
                response["data"]["humidity_percent"]
            ),
        }