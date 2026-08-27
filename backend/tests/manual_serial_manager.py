"""Manual COM5 protocol check; intentionally excluded from pytest."""

from backend.hardware.serial_manager import SerialManager


cypher = SerialManager(
    port="COM5"
)

try:
    cypher.connect()

    distance = cypher.send_command(
        "GET_DISTANCE"
    )

    light = cypher.send_command(
        "GET_LIGHT"
    )

    climate = cypher.send_command(
        "GET_CLIMATE"
    )

    print()
    print("Distance:")
    print(distance)

    print()
    print("Light:")
    print(light)

    print()
    print("Climate:")
    print(climate)

finally:
    cypher.disconnect()
