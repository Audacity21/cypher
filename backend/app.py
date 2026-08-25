from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.hardware import CypherHardware
from backend.sensor_stream import SensorStream


hardware = CypherHardware(
    port="COM5"
)

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

    print("Radar client connected.")

    try:
        async for sensor_data in sensor_stream.distance_stream():
            await websocket.send_json(sensor_data)

    except WebSocketDisconnect:
        print("Radar client disconnected.")

    except Exception as error:
        print(f"WebSocket error: {error}")