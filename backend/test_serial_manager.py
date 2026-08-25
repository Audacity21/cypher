from serial_manager import SerialManager


cypher = SerialManager(port="COM5")

try:
    cypher.connect()

    # First prove normal commands still work.
    response = cypher.send_command("PING")

    print()
    print("PING response:")
    print(response)

    print()
    print("Waiting for Arduino event...")

    event = cypher.get_event(timeout=10)

    if event:
        print()
        print("EVENT RECEIVED:")
        print(event)
    else:
        print("No event received.")

finally:
    cypher.disconnect()