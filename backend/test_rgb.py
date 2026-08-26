import time

from backend.hardware import CypherHardware


cypher = CypherHardware(
    port="COM5"
)

try:
    cypher.connect()

    print()
    print("RED")

    print(
        cypher.set_rgb(
            60,
            0,
            0,
        )
    )

    time.sleep(2)

    print()
    print("GREEN")

    print(
        cypher.set_rgb(
            0,
            60,
            0,
        )
    )

    time.sleep(2)

    print()
    print("BLUE")

    print(
        cypher.set_rgb(
            0,
            0,
            60,
        )
    )

    time.sleep(2)

    print()
    print("CYAN")

    print(
        cypher.set_rgb(
            0,
            60,
            60,
        )
    )

    time.sleep(2)

    print()
    print("PURPLE")

    print(
        cypher.set_rgb(
            40,
            0,
            60,
        )
    )

    time.sleep(2)

    print()
    print("WHITE")

    print(
        cypher.set_rgb(
            60,
            60,
            60,
        )
    )

    time.sleep(2)

    print()
    print("OFF")

    print(
        cypher.rgb_off()
    )

finally:
    cypher.disconnect()