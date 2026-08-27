import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.actions.action_engine import ActionEngine
from backend.actions.behavior_engine import BehaviorEngine
from backend.hardware.hardware import CypherHardware
from backend.intelligence.intelligence_engine import IntelligenceEngine
from backend.intelligence.intelligence_guard import IntelligenceGuard
from backend.intelligence.ollama_intelligence import OllamaIntelligence
from backend.intelligence.shadow_metrics import ShadowMetrics
from backend.perception.event_engine import EventEngine
from backend.perception.sensor_stream import SensorStream
from backend.perception.world_state_manager import WorldStateManager
from backend.runtime import CypherRuntime


hardware = CypherHardware(port="COM5")
sensor_stream = SensorStream(hardware=hardware, interval=0.25)
world_state = WorldStateManager()
event_engine = EventEngine()
intelligence_engine = IntelligenceEngine()
shadow_intelligence = OllamaIntelligence()
intelligence_guard = IntelligenceGuard(minimum_confidence=0.70)
shadow_metrics = ShadowMetrics()
action_engine = ActionEngine(hardware)
behavior_engine = BehaviorEngine(action_engine)

runtime = CypherRuntime(
    sensor_stream=sensor_stream,
    world_state=world_state,
    event_engine=event_engine,
    intelligence_engine=intelligence_engine,
    intelligence_guard=intelligence_guard,
    shadow_intelligence=shadow_intelligence,
    shadow_metrics=shadow_metrics,
    behavior_engine=behavior_engine,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Cypher backend...")
    hardware.connect()
    print("Cypher hardware ready.")

    try:
        print("[CYPHER ACTION]", action_engine.idle())
    except Exception as error:
        print("[CYPHER ACTION ERROR]", error)

    runtime_task = asyncio.create_task(runtime.run(), name="cypher-runtime")
    shadow_task = asyncio.create_task(
        runtime.run_shadow_worker(),
        name="cypher-shadow-worker",
    )

    try:
        yield
    finally:
        print("Stopping Cypher backend...")
        runtime_task.cancel()
        shadow_task.cancel()
        with suppress(asyncio.CancelledError):
            await runtime_task
        with suppress(asyncio.CancelledError):
            await shadow_task

        try:
            action_engine.off()
        except Exception as error:
            print("[CYPHER ACTION ERROR]", error)
        hardware.disconnect()


app = FastAPI(title="Cypher", lifespan=lifespan)


@app.get("/")
async def root():
    return {
        "name": "CYPHER",
        "status": "online",
        "architecture": "autonomous-guarded-shadow-v1",
        "llm": "qwen2.5:1.5b",
        "llm_mode": "shadow",
        "guard": "enabled",
        "minimum_confidence": intelligence_guard.minimum_confidence,
    }


@app.get("/state")
async def get_state():
    return world_state.get_current_dict()


@app.get("/action/status")
async def get_action_status():
    return {"status": action_engine.get_status()}


@app.get("/intelligence/shadow")
async def get_shadow_metrics():
    return shadow_metrics.to_dict()


@app.websocket("/ws/sensors")
async def websocket_sensors(websocket: WebSocket):
    await websocket.accept()
    queue = runtime.subscribe()
    print("Cypher UI connected.")

    try:
        # A newly connected HUD receives a coherent snapshot immediately.
        await websocket.send_json(
            {
                "type": "world_state",
                "data": world_state.get_current_dict(),
            }
        )
        await websocket.send_json(
            {
                "type": "shadow_metrics",
                "data": shadow_metrics.to_dict(),
            }
        )

        while True:
            await websocket.send_json(await queue.get())
    except WebSocketDisconnect:
        print("Cypher UI disconnected.")
    except Exception as error:
        print(f"WebSocket error: {error}")
    finally:
        runtime.unsubscribe(queue)
