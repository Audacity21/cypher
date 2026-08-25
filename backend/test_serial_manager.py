from serial_manager import SerialManager


cypher = SerialManager(port="COM5")

try:
    cypher.connect()

    response = cypher.send_command(
        "GET_DISTANCE"
    )

    print()
    print("Distance response:")
    print(response)

finally:
    cypher.disconnect()