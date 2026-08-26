from backend.hardware.hardware import CypherHardware


class ActionEngine:
    """
    Converts semantic Cypher actions into
    physical hardware commands.

    Higher layers should request meanings such as
    ALERT or IDLE rather than controlling pins.
    """

    MAX_BRIGHTNESS = 60

    COLORS = {
        "OFF": (0, 0, 0),

        # Cypher default
        "IDLE": (45, 45, 45),

        # AI / processing later
        "THINKING": (40, 0, 60),

        # Attention required
        "ALERT": (60, 0, 0),

        # Successful action
        "SUCCESS": (0, 60, 0),

        # Something nearby
        "PRESENCE": (0, 0, 60),

        # Environment became dark
        "DARK": (25, 0, 60),
    }

    def __init__(
        self,
        hardware: CypherHardware,
    ):
        self.hardware = hardware
        self.current_status = "OFF"

    def set_status(
        self,
        status: str,
    ) -> dict:
        status = status.upper()

        if status not in self.COLORS:
            raise ValueError(
                f"Unknown Cypher status: {status}"
            )

        red, green, blue = self.COLORS[
            status
        ]

        # Final software-side brightness guard.
        red = min(
            red,
            self.MAX_BRIGHTNESS,
        )

        green = min(
            green,
            self.MAX_BRIGHTNESS,
        )

        blue = min(
            blue,
            self.MAX_BRIGHTNESS,
        )

        result = self.hardware.set_rgb(
            red,
            green,
            blue,
        )

        self.current_status = status

        return {
            "status": status,
            "rgb": result,
        }

    def off(self) -> dict:
        return self.set_status(
            "OFF"
        )

    def idle(self) -> dict:
        return self.set_status(
            "IDLE"
        )

    def thinking(self) -> dict:
        return self.set_status(
            "THINKING"
        )

    def alert(self) -> dict:
        return self.set_status(
            "ALERT"
        )

    def success(self) -> dict:
        return self.set_status(
            "SUCCESS"
        )

    def presence(self) -> dict:
        return self.set_status(
            "PRESENCE"
        )

    def dark(self) -> dict:
        return self.set_status(
            "DARK"
        )

    def get_status(
        self,
    ) -> str:
        return self.current_status