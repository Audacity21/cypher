from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.hardware import CypherHardware
from backend.sensor_stream import SensorStream
from backend.world_state_manager import WorldStateManager
from backend.event_engine import EventEngine


hardware = CypherHardware(
    port="COM5"
)

sensor_stream = SensorStream(
    hardware=hardware,
    interval=0.25,
)

world_state = WorldStateManager()
event_engine = EventEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Cypher backend...")

    hardware.connect()

    print("Cypher hardware ready.")

    yield

    print("Stopping Cypher backend...")

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
    return world_state.get_current_dict()


@app.websocket("/ws/sensors")
async def websocket_sensors(
    websocket: WebSocket,
):
    await websocket.accept()

    print("Cypher UI connected.")

    try:
        async for sensor_message in sensor_stream.sensor_stream():

            if (
                sensor_message.get("type")
                != "sensor_state"
            ):
                await websocket.send_json(
                    sensor_message
                )
                continue

            sensor_data = sensor_message[
                "data"
            ]

            current_state = (
                world_state.update(
                    sensor_data
                )
            )

            events = event_engine.evaluate(
                world_state.get_previous(),
                current_state,
            )

            await websocket.send_json(
                {
                    "type": "world_state",
                    "data": current_state.to_dict(),
                }
            )

            for event in events:
                print(
                    f"[CYPHER EVENT] "
                    f"{event['event']} "
                    f"{event['data']}"
                )

                await websocket.send_json(event)

    except WebSocketDisconnect:
        print(
            "Cypher UI disconnected."
        )

    except Exception as error:
        print(
            f"WebSocket error: {error}"
        )