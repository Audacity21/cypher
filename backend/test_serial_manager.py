from serial_manager import SerialManager


cypher = SerialManager(port="COM5")

try:
    cypher.connect()

    distance = cypher.send_command(
        "GET_DISTANCE"
    )

    light = cypher.send_command(
        "GET_LIGHT"
    )

    print()
    print("Distance:")
    print(distance)

    print()
    print("Light:")
    print(light)

finally:
    cypher.disconnect()