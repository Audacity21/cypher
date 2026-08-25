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
                response.get("error", "Unknown distance sensor error")
            )

        return float(response["data"]["distance_cm"])