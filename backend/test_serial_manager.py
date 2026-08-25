import time

from serial_manager import SerialManager


cypher = SerialManager(port="COM5")

try:
    cypher.connect()

    print("Streaming distance. Press Ctrl+C to stop.\n")

    while True:
        response = cypher.send_command("GET_DISTANCE")

        if response.get("ok"):
            distance = response["data"]["distance_cm"]

            print(f"Distance: {distance:.2f} cm")

        else:
            print(
                "Distance error:",
                response.get("error"),
            )

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopping distance stream...")

finally:
    cypher.disconnect()