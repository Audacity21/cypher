import asyncio
import time

from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field

from backend.actions.action_engine import ActionEngine
from backend.actions.behavior_engine import BehaviorEngine
from backend.agent.conversation_agent import ConversationAgent
from backend.alarms.alarm_service import AlarmService
from backend.perception.event_engine import EventEngine
from backend.hardware.hardware import CypherHardware
from backend.intelligence.intelligence_engine import IntelligenceEngine
from backend.intelligence.authority_policy import AuthorityPolicy
from backend.intelligence.intelligence_guard import IntelligenceGuard
from backend.intelligence.llm_provider import OllamaProvider
from backend.intelligence.ollama_intelligence import OllamaIntelligence
from backend.perception.sensor_stream import SensorStream
from backend.intelligence.shadow_metrics import ShadowMetrics
from backend.perception.world_state_manager import WorldStateManager
from backend.persistence.alarm_repository import AlarmRepository
from backend.persistence.conversation_repository import ConversationRepository
from backend.persistence.database import CypherDatabase
from backend.persistence.memory_repository import MemoryRepository


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

# Qwen remains shadow-only.
shadow_intelligence = OllamaIntelligence()

# Safety gate for LLM decisions.
intelligence_guard = IntelligenceGuard(
    minimum_confidence=0.70
)

# Narrow permission gate applied only after IntelligenceGuard.
authority_policy = AuthorityPolicy(
    minimum_authority_confidence=0.85
)

# Evaluation telemetry.
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
# PERSISTENCE / SCHEDULER
# ============================================================

database = CypherDatabase(
    Path(__file__).parent / "data" / "cypher.db"
)

alarm_repository = AlarmRepository(database)
conversation_repository = ConversationRepository(database)
memory_repository = MemoryRepository(database)

alarm_service = AlarmService(
    alarms=alarm_repository,
    actions=action_engine,
)

conversation_agent = ConversationAgent(
    conversations=conversation_repository,
    memories=memory_repository,
    alarms=alarm_repository,
    world_state=world_state,
    hardware=hardware,
    llm=OllamaProvider(model="qwen2.5:1.5b"),
)


class TimerRequest(BaseModel):
    seconds: float = Field(gt=0, le=86400)
    label: str = Field(default="Cypher timer", max_length=200)


class AgentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None


# ============================================================
# LIFESPAN
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

    alarm_task = asyncio.create_task(
        alarm_service.run(),
        name="cypher-alarm-service",
    )

    try:
        yield
    finally:
        alarm_task.cancel()
        with suppress(asyncio.CancelledError):
            await alarm_task

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
# HTTP
# ============================================================

@app.get("/")
async def root():
    return {
        "name": "CYPHER",
        "status": "online",
        "architecture":
            "limited-ai-authority-v1",
        "llm":
            "qwen2.5:1.5b",
        "llm_mode":
            "limited_authority",
        "guard":
            "enabled",
        "minimum_confidence":
            intelligence_guard.minimum_confidence,

        "minimum_authority_confidence":
            authority_policy.minimum_authority_confidence,
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


@app.post("/timers")
async def create_timer(request: TimerRequest):
    return await asyncio.to_thread(
        alarm_repository.create,
        kind="timer",
        label=request.label,
        trigger_at=time.time() + request.seconds,
    )


@app.get("/alarms")
async def list_alarms():
    return await asyncio.to_thread(alarm_repository.list)


@app.delete("/alarms/{alarm_id}")
async def cancel_alarm(alarm_id: str):
    alarm = await asyncio.to_thread(
        alarm_repository.cancel,
        alarm_id,
    )
    if alarm is None:
        raise HTTPException(status_code=404, detail="Alarm not found")
    return alarm


@app.post("/alarms/stop")
async def stop_alarms():
    completed = await asyncio.to_thread(
        alarm_repository.complete_fired
    )
    action = await asyncio.to_thread(action_engine.idle)
    await asyncio.to_thread(action_engine.stop_sound)
    return {
        "completed": completed,
        "action": action,
    }


@app.post("/agent/message")
async def agent_message(request: AgentRequest):
    try:
        return await asyncio.to_thread(
            conversation_agent.handle,
            text=request.text,
            conversation_id=request.conversation_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/conversations/{conversation_id}/messages")
async def conversation_history(conversation_id: str):
    if conversation_repository.get(conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await asyncio.to_thread(
        conversation_repository.history,
        conversation_id,
    )


# ============================================================
# WEBSOCKET
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
            # NON-WORLD-STATE MESSAGE
            # =================================================

            if (
                sensor_message.get("type")
                != "sensor_state"
            ):
                await websocket.send_json(
                    sensor_message
                )

                continue


            # =================================================
            # WORLD STATE
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
            # EVENTS
            # =================================================

            events = (
                event_engine.evaluate(
                    previous_state,
                    current_state,
                )
            )


            await websocket.send_json(
                {
                    "type":
                        "world_state",

                    "data":
                        current_state_dict,
                }
            )


            # =================================================
            # EVENT PIPELINE
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
                # AUTHORITATIVE DETERMINISTIC INTELLIGENCE
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

                    # Deterministic fallback remains selected unless Qwen
                    # passes both the guard and the narrower authority policy.
                    authoritative_decision = decision
                    authority_source = "deterministic"
                    authority_reason = "deterministic_fallback"


                    # =========================================
                    # SHADOW QWEN
                    # =========================================

                    try:
                        shadow_decision = (
                            await asyncio.to_thread(
                                shadow_intelligence.decide,
                                event,
                                current_state_dict,
                            )
                        )


                        # -------------------------------------
                        # GUARD
                        # -------------------------------------

                        guard_result = (
                            intelligence_guard.evaluate(
                                shadow_decision
                            )
                        )

                        authority_result = (
                            authority_policy.evaluate(
                                intent=shadow_decision.intent,
                                confidence=shadow_decision.confidence,
                                guard_allowed=guard_result.allowed,
                            )
                        )

                        if authority_result.allowed:
                            authoritative_decision = shadow_decision
                            authority_source = "ai"

                        authority_reason = authority_result.reason


                        # -------------------------------------
                        # AGREEMENT
                        # -------------------------------------

                        agreement = (
                            decision.intent
                            == shadow_decision.intent
                        )


                        # -------------------------------------
                        # METRICS
                        # -------------------------------------

                        shadow_metrics.record(
                            authoritative_intent=
                                decision.intent,

                            shadow_intent=
                                shadow_decision.intent,

                            shadow_confidence=
                                shadow_decision.confidence,

                            guard_allowed=
                                guard_result.allowed,

                            guard_reason=
                                guard_result.reason,
                        )


                        # -------------------------------------
                        # LOG SHADOW DECISION
                        # -------------------------------------

                        print(
                            "[CYPHER SHADOW]",
                            {
                                "intent":
                                    shadow_decision.intent,

                                "reason":
                                    shadow_decision.reason,

                                "confidence":
                                    shadow_decision.confidence,

                                "agreement":
                                    agreement,
                            },
                        )


                        # -------------------------------------
                        # LOG GUARD
                        # -------------------------------------

                        print(
                            "[CYPHER GUARD]",
                            {
                                "allowed":
                                    guard_result.allowed,

                                "reason":
                                    guard_result.reason,
                            },
                        )

                        print(
                            "[CYPHER AUTHORITY]",
                            {
                                "allowed":
                                    authority_result.allowed,

                                "reason":
                                    authority_result.reason,

                                "source":
                                    authority_source,
                            },
                        )


                        print(
                            "[CYPHER SHADOW METRICS]",
                            shadow_metrics.to_dict(),
                        )


                        # -------------------------------------
                        # SEND SHADOW DECISION
                        # -------------------------------------

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

                                    "agreement":
                                        agreement,

                                    "model":
                                        "qwen2.5:1.5b",

                                    "guard_allowed":
                                        guard_result.allowed,

                                    "guard_reason":
                                        guard_result.reason,
                                },
                            }
                        )


                        # -------------------------------------
                        # SEND METRICS
                        # -------------------------------------

                        await websocket.send_json(
                            {
                                "type":
                                    "shadow_metrics",

                                "data":
                                    shadow_metrics.to_dict(),
                            }
                        )


                        # Authority remains restricted to the policy allowlist.
                        # ALERT and every unknown intent fall back to rules.


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
                    # AUTHORITATIVE VALIDATION
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
                    # BEHAVIOR
                    #
                    # Guarded/policy-approved Qwen decisions may
                    # control only the limited authority allowlist.
                    # Every other path retains deterministic control.
                    # =========================================

                    action_result = (
                        await asyncio.to_thread(
                            behavior_engine.handle_decision,
                            authoritative_decision,
                        )
                    )


                    # =========================================
                    # ACTION
                    # =========================================

                    if action_result:

                        print(
                            "[CYPHER ACTION]",
                            {
                                "source":
                                    authority_source,

                                "authority_reason":
                                    authority_reason,

                                "result":
                                    action_result,
                            },
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
