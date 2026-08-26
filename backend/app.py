import asyncio

from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
)

from backend.action_engine import ActionEngine
from backend.behavior_engine import BehaviorEngine
from backend.event_engine import EventEngine
from backend.hardware import CypherHardware
from backend.intelligence_engine import IntelligenceEngine
from backend.ollama_intelligence import OllamaIntelligence
from backend.sensor_stream import SensorStream
from backend.shadow_metrics import ShadowMetrics
from backend.world_state_manager import WorldStateManager


# ============================================================
# HARDWARE
# ============================================================

hardware = CypherHardware(
    port="COM5"
)


# ============================================================
# PERCEPTION
# ============================================================

sensor_stream = SensorStream(
    hardware=hardware,
    interval=0.25,
)

world_state = WorldStateManager()

event_engine = EventEngine()


# ============================================================
# INTELLIGENCE
# ============================================================

# Deterministic intelligence remains authoritative.
intelligence_engine = IntelligenceEngine()

# Local Qwen model runs in shadow mode.
shadow_intelligence = OllamaIntelligence()

# Tracks how often Qwen agrees with the deterministic engine.
shadow_metrics = ShadowMetrics()


# ============================================================
# ACTIONS
# ============================================================

action_engine = ActionEngine(
    hardware
)

behavior_engine = BehaviorEngine(
    action_engine
)


# ============================================================
# APP LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    print(
        "Starting Cypher backend..."
    )

    hardware.connect()

    print(
        "Cypher hardware ready."
    )

    try:
        action_result = (
            action_engine.idle()
        )

        print(
            "[CYPHER ACTION]",
            action_result,
        )

    except Exception as error:
        print(
            "[CYPHER ACTION ERROR]",
            error,
        )

    yield

    print(
        "Stopping Cypher backend..."
    )

    try:
        action_engine.off()

    except Exception as error:
        print(
            "[CYPHER ACTION ERROR]",
            error,
        )

    hardware.disconnect()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Cypher",
    lifespan=lifespan,
)


# ============================================================
# HTTP ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    return {
        "name": "CYPHER",
        "status": "online",
        "architecture":
            "intelligence-shadow-v1",
        "llm":
            "qwen2.5:1.5b",
        "llm_mode":
            "shadow",
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


@app.get("/intelligence/shadow")
async def get_shadow_metrics():
    return shadow_metrics.to_dict()


# ============================================================
# SENSOR WEBSOCKET
# ============================================================

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

            # =================================================
            # SENSOR ERROR / OTHER MESSAGE
            # =================================================

            if (
                sensor_message.get(
                    "type"
                )
                != "sensor_state"
            ):
                await websocket.send_json(
                    sensor_message
                )

                continue


            # =================================================
            # WORLD STATE UPDATE
            # =================================================

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

            current_state_dict = (
                current_state.to_dict()
            )


            # =================================================
            # EVENT ENGINE
            # =================================================

            events = (
                event_engine.evaluate(
                    previous_state,
                    current_state,
                )
            )


            # =================================================
            # SEND WORLD STATE TO UI
            # =================================================

            await websocket.send_json(
                {
                    "type":
                        "world_state",

                    "data":
                        current_state_dict,
                }
            )


            # =================================================
            # PROCESS EVENTS
            # =================================================

            for event in events:

                print(
                    f"[CYPHER EVENT] "
                    f"{event['event']} "
                    f"{event['data']}"
                )

                await websocket.send_json(
                    event
                )


                # =============================================
                # AUTHORITATIVE INTELLIGENCE
                # =============================================

                try:
                    decision = (
                        intelligence_engine.decide(
                            event=event,
                            world_state=(
                                current_state_dict
                            ),
                        )
                    )

                    valid = (
                        intelligence_engine.validate(
                            decision
                        )
                    )

                    print(
                        "[CYPHER INTELLIGENCE]",
                        {
                            "intent":
                                decision.intent,

                            "reason":
                                decision.reason,

                            "confidence":
                                decision.confidence,

                            "valid":
                                valid,
                        },
                    )

                    await websocket.send_json(
                        {
                            "type":
                                "intelligence",

                            "mode":
                                "authoritative",

                            "decision": {
                                "intent":
                                    decision.intent,

                                "reason":
                                    decision.reason,

                                "confidence":
                                    decision.confidence,

                                "valid":
                                    valid,
                            },
                        }
                    )


                    # =========================================
                    # SHADOW QWEN INTELLIGENCE
                    # =========================================

                    try:
                        shadow_decision = (
                            await asyncio.to_thread(
                                shadow_intelligence.decide,
                                event,
                                current_state_dict,
                            )
                        )

                        shadow_valid = (
                            shadow_intelligence.validate(
                                shadow_decision
                            )
                        )

                        agreement = (
                            decision.intent
                            == shadow_decision.intent
                        )

                        shadow_metrics.record(
                            authoritative_intent=
                                decision.intent,

                            shadow_intent=
                                shadow_decision.intent,

                            shadow_confidence=
                                shadow_decision.confidence,
                        )

                        print(
                            "[CYPHER SHADOW]",
                            {
                                "intent":
                                    shadow_decision.intent,

                                "reason":
                                    shadow_decision.reason,

                                "confidence":
                                    shadow_decision.confidence,

                                "valid":
                                    shadow_valid,

                                "agreement":
                                    agreement,
                            },
                        )

                        print(
                            "[CYPHER SHADOW METRICS]",
                            shadow_metrics.to_dict(),
                        )

                        await websocket.send_json(
                            {
                                "type":
                                    "shadow_intelligence",

                                "decision": {
                                    "intent":
                                        shadow_decision.intent,

                                    "reason":
                                        shadow_decision.reason,

                                    "confidence":
                                        shadow_decision.confidence,

                                    "valid":
                                        shadow_valid,

                                    "agreement":
                                        agreement,

                                    "model":
                                        "qwen2.5:1.5b",
                                },
                            }
                        )

                        await websocket.send_json(
                            {
                                "type":
                                    "shadow_metrics",

                                "data":
                                    shadow_metrics.to_dict(),
                            }
                        )


                    except Exception as error:
                        print(
                            "[CYPHER SHADOW ERROR]",
                            error,
                        )

                        await websocket.send_json(
                            {
                                "type":
                                    "shadow_error",

                                "error":
                                    str(error),
                            }
                        )


                    # =========================================
                    # AUTHORITY VALIDATION GATE
                    # =========================================

                    if not valid:
                        print(
                            "[CYPHER INTELLIGENCE BLOCKED]",
                            {
                                "intent":
                                    decision.intent,

                                "reason":
                                    decision.reason,
                            },
                        )

                        continue


                    # =========================================
                    # BEHAVIOR ENGINE
                    #
                    # Only the deterministic decision reaches
                    # this point.
                    # =========================================

                    action_result = (
                        await asyncio.to_thread(
                            behavior_engine.handle_decision,
                            decision,
                        )
                    )


                    # =========================================
                    # ACTION RESULT
                    # =========================================

                    if action_result:
                        print(
                            "[CYPHER ACTION]",
                            action_result,
                        )

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
                        "[CYPHER INTELLIGENCE ERROR]",
                        error,
                    )

                    await websocket.send_json(
                        {
                            "type":
                                "intelligence_error",

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