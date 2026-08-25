from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.hardware import CypherHardware
from backend.sensor_stream import SensorStream


hardware = CypherHardware(port="COM5")

sensor_stream = SensorStream(
    hardware=hardware,
    interval=0.1,
)


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


@app.websocket("/ws/sensors")
async def websocket_sensors(
    websocket: WebSocket,
):
    await websocket.accept()

    print("Cypher UI connected.")

    try:
        async for state in sensor_stream.sensor_stream():
            await websocket.send_json(state)

    except WebSocketDisconnect:
        print("Cypher UI disconnected.")

    except Exception as error:
        print(f"WebSocket error: {error}")