"""Manual COM5/RGB integration check; intentionally excluded from pytest."""

import time

from backend.actions.action_engine import ActionEngine
from backend.hardware.hardware import CypherHardware


hardware = CypherHardware(
    port="COM5"
)

actions = ActionEngine(
    hardware
)

try:
    hardware.connect()

    print("IDLE")
    print(
        actions.idle()
    )
    time.sleep(2)

    print("THINKING")
    print(
        actions.thinking()
    )
    time.sleep(2)

    print("ALERT")
    print(
        actions.alert()
    )
    time.sleep(2)

    print("SUCCESS")
    print(
        actions.success()
    )
    time.sleep(2)

    print("PRESENCE")
    print(
        actions.presence()
    )
    time.sleep(2)

    print("DARK")
    print(
        actions.dark()
    )
    time.sleep(2)

    print("OFF")
    print(
        actions.off()
    )

finally:
    # Always try to leave the indicator off.
    try:
        actions.off()
    except Exception:
        pass

    hardware.disconnect()
