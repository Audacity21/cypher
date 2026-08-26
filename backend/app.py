import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.action_engine import ActionEngine
from backend.behavior_engine import BehaviorEngine
from backend.event_engine import EventEngine
from backend.hardware import CypherHardware
from backend.sensor_stream import SensorStream
from backend.world_state_manager import WorldStateManager


hardware = CypherHardware(
    port="COM5"
)

sensor_stream = SensorStream(
    hardware=hardware,
    interval=0.25,
)

world_state = WorldStateManager()

event_engine = EventEngine()

action_engine = ActionEngine(
    hardware
)

behavior_engine = BehaviorEngine(
    action_engine
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Cypher backend...")

    hardware.connect()

    print("Cypher hardware ready.")

    try:
        action_engine.idle()

        print(
            "[CYPHER ACTION]",
            "IDLE",
        )

    except Exception as error:
        print(
            "[CYPHER ACTION ERROR]",
            error,
        )

    yield

    print("Stopping Cypher backend...")

    try:
        action_engine.off()

    except Exception as error:
        print(
            "[CYPHER ACTION ERROR]",
            error,
        )

    hardware.disconnect()


app = FastAPI(
    title="Cypher",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "name": "CYPHER",
        "status": "online",
    }


@app.get("/state")
async def get_state():
    return (
        world_state.get_current_dict()
    )


@app.get("/action/status")
async def get_action_status():
    return {
        "status":
            action_engine.get_status()
    }


@app.websocket("/ws/sensors")
async def websocket_sensors(
    websocket: WebSocket,
):
    await websocket.accept()

    print(
        "Cypher UI connected."
    )

    try:
        async for sensor_message in (
            sensor_stream.sensor_stream()
        ):

            # ---------------------------------------------
            # SENSOR ERRORS / NON-STATE MESSAGES
            # ---------------------------------------------

            if (
                sensor_message.get("type")
                != "sensor_state"
            ):
                await websocket.send_json(
                    sensor_message
                )

                continue

            # ---------------------------------------------
            # UPDATE WORLD STATE
            # ---------------------------------------------

            sensor_data = (
                sensor_message["data"]
            )

            current_state = (
                world_state.update(
                    sensor_data
                )
            )

            previous_state = (
                world_state.get_previous()
            )

            # ---------------------------------------------
            # EVENT DETECTION
            # ---------------------------------------------

            events = (
                event_engine.evaluate(
                    previous_state,
                    current_state,
                )
            )

            # ---------------------------------------------
            # SEND WORLD STATE TO UI
            # ---------------------------------------------

            await websocket.send_json(
                {
                    "type": "world_state",
                    "data":
                        current_state.to_dict(),
                }
            )

            # ---------------------------------------------
            # HANDLE EVENTS
            # ---------------------------------------------

            for event in events:

                print(
                    f"[CYPHER EVENT] "
                    f"{event['event']} "
                    f"{event['data']}"
                )

                # Send semantic event to UI.
                await websocket.send_json(
                    event
                )

                # Let behavior layer decide
                # whether the event needs a
                # physical response.
                try:
                    action_result = (
                        await asyncio.to_thread(
                            behavior_engine.handle_event,
                            event,
                        )
                    )

                    if action_result:
                        print(
                            "[CYPHER ACTION]",
                            action_result,
                        )

                        # Also expose the action
                        # to the frontend.
                        await websocket.send_json(
                            {
                                "type":
                                    "action",

                                "action":
                                    action_result,
                            }
                        )

                except Exception as error:
                    print(
                        "[CYPHER ACTION ERROR]",
                        error,
                    )

                    await websocket.send_json(
                        {
                            "type":
                                "action_error",

                            "error":
                                str(error),
                        }
                    )

    except WebSocketDisconnect:
        print(
            "Cypher UI disconnected."
        )

    except Exception as error:
        print(
            f"WebSocket error: {error}"
        )