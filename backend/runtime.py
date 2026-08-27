import asyncio
from contextlib import suppress
from dataclasses import dataclass

from backend.actions.behavior_engine import BehaviorEngine
from backend.intelligence.authority_policy import AuthorityPolicy, AuthorityResult
from backend.intelligence.intelligence_engine import IntelligenceEngine
from backend.intelligence.intelligence_guard import IntelligenceGuard
from backend.intelligence.ollama_intelligence import OllamaIntelligence
from backend.intelligence.shadow_metrics import ShadowMetrics
from backend.perception.event_engine import EventEngine
from backend.perception.sensor_stream import SensorStream
from backend.perception.world_state_manager import WorldStateManager


@dataclass(frozen=True)
class ShadowWork:
    event: dict
    world_state: dict
    authoritative_intent: str
    generation: int


class CypherRuntime:
    """Owns the single autonomous perception-to-action loop."""

    def __init__(
        self,
        *,
        sensor_stream: SensorStream,
        world_state: WorldStateManager,
        event_engine: EventEngine,
        intelligence_engine: IntelligenceEngine,
        intelligence_guard: IntelligenceGuard,
        authority_policy: AuthorityPolicy,
        shadow_intelligence: OllamaIntelligence,
        shadow_metrics: ShadowMetrics,
        behavior_engine: BehaviorEngine,
        subscriber_queue_size: int = 100,
    ):
        self.sensor_stream = sensor_stream
        self.world_state = world_state
        self.event_engine = event_engine
        self.intelligence_engine = intelligence_engine
        self.intelligence_guard = intelligence_guard
        self.authority_policy = authority_policy
        self.shadow_intelligence = shadow_intelligence
        self.shadow_metrics = shadow_metrics
        self.behavior_engine = behavior_engine
        self.subscriber_queue_size = subscriber_queue_size
        self._subscribers: set[asyncio.Queue] = set()
        self._shadow_queue: asyncio.Queue[ShadowWork] = asyncio.Queue(maxsize=1)
        self._event_generation = 0

    def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue(maxsize=self.subscriber_queue_size)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    async def broadcast(self, message: dict) -> None:
        for queue in tuple(self._subscribers):
            if queue.full():
                with suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            queue.put_nowait(message)

    async def run(self) -> None:
        async for sensor_message in self.sensor_stream.sensor_stream():
            try:
                await self._handle_sensor_message(sensor_message)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                print("[CYPHER RUNTIME ERROR]", error)
                await self.broadcast({"type": "runtime_error", "error": str(error)})

    async def _handle_sensor_message(self, sensor_message: dict) -> None:
        if sensor_message.get("type") != "sensor_state":
            await self.broadcast(sensor_message)
            return

        current_state = self.world_state.update(sensor_message["data"])
        previous_state = self.world_state.get_previous()
        current_state_dict = current_state.to_dict()
        await self.broadcast({"type": "world_state", "data": current_state_dict})

        for event in self.event_engine.evaluate(previous_state, current_state):
            await self._handle_event(event, current_state_dict)

    async def _handle_event(self, event: dict, current_state: dict) -> None:
        self._event_generation += 1
        generation = self._event_generation
        print(f"[CYPHER EVENT] {event['event']} {event['data']}")
        await self.broadcast(event)

        try:
            decision = self.intelligence_engine.decide(
                event=event,
                world_state=current_state,
            )
            valid = self.intelligence_engine.validate(decision)
            decision_payload = {
                "intent": decision.intent,
                "reason": decision.reason,
                "confidence": decision.confidence,
                "valid": valid,
            }
            print("[CYPHER INTELLIGENCE]", decision_payload)
            await self.broadcast(
                {
                    "type": "intelligence",
                    "mode": "authoritative",
                    "decision": decision_payload,
                }
            )

            if not valid:
                print("[CYPHER INTELLIGENCE BLOCKED]", decision_payload)
                return

            # Deterministic behavior happens before any LLM work.
            action_result = await asyncio.to_thread(
                self.behavior_engine.handle_decision,
                decision,
            )
            if action_result:
                print("[CYPHER ACTION]", action_result)
                await self.broadcast(
                    {
                        "type": "action",
                        "source": "deterministic",
                        "action": action_result,
                    }
                )

            self._enqueue_shadow(
                ShadowWork(
                    event=event,
                    world_state=current_state,
                    authoritative_intent=decision.intent,
                    generation=generation,
                )
            )
        except Exception as error:
            print("[CYPHER INTELLIGENCE ERROR]", error)
            await self.broadcast(
                {"type": "intelligence_error", "error": str(error)}
            )

    def _enqueue_shadow(self, work: ShadowWork) -> None:
        # A slow model must not accumulate decisions about stale sensor state.
        if self._shadow_queue.full():
            with suppress(asyncio.QueueEmpty):
                self._shadow_queue.get_nowait()
                self._shadow_queue.task_done()
        self._shadow_queue.put_nowait(work)

    async def run_shadow_worker(self) -> None:
        while True:
            work = await self._shadow_queue.get()
            try:
                await self._evaluate_shadow(work)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                print("[CYPHER SHADOW ERROR]", error)
                await self.broadcast({"type": "shadow_error", "error": str(error)})
            finally:
                self._shadow_queue.task_done()

    async def _evaluate_shadow(self, work: ShadowWork) -> None:
        shadow_decision = await asyncio.to_thread(
            self.shadow_intelligence.decide,
            work.event,
            work.world_state,
        )
        guard_result = self.intelligence_guard.evaluate(shadow_decision)
        agreement = work.authoritative_intent == shadow_decision.intent
        authority_result = self.authority_policy.evaluate(
            intent=shadow_decision.intent,
            confidence=shadow_decision.confidence,
            guard_allowed=guard_result.allowed,
        )

        if authority_result.allowed and work.generation != self._event_generation:
            authority_result = AuthorityResult(
                allowed=False,
                reason="stale_shadow_decision",
            )

        print(
            "[CYPHER SHADOW]",
            {
                "intent": shadow_decision.intent,
                "reason": shadow_decision.reason,
                "confidence": shadow_decision.confidence,
                "agreement": agreement,
            },
        )
        print(
            "[CYPHER GUARD]",
            {"allowed": guard_result.allowed, "reason": guard_result.reason},
        )
        if authority_result.allowed and not agreement:
            try:
                action_result = await asyncio.to_thread(
                    self.behavior_engine.handle_decision,
                    shadow_decision,
                )
                if action_result:
                    print("[CYPHER AI ACTION]", action_result)
                    await self.broadcast(
                        {
                            "type": "action",
                            "source": "ai",
                            "action": action_result,
                        }
                    )
            except Exception as error:
                authority_result = AuthorityResult(
                    allowed=False,
                    reason="ai_action_failed",
                )
                print("[CYPHER AI ACTION ERROR]", error)
                await self.broadcast(
                    {
                        "type": "action_error",
                        "source": "ai",
                        "error": str(error),
                    }
                )

        self.shadow_metrics.record(
            authoritative_intent=work.authoritative_intent,
            shadow_intent=shadow_decision.intent,
            shadow_confidence=shadow_decision.confidence,
            guard_allowed=guard_result.allowed,
            guard_reason=guard_result.reason,
            authority_allowed=authority_result.allowed,
            authority_reason=authority_result.reason,
        )
        print(
            "[CYPHER AUTHORITY]",
            {
                "allowed": authority_result.allowed,
                "reason": authority_result.reason,
            },
        )

        await self.broadcast(
            {
                "type": "shadow_intelligence",
                "decision": {
                    "intent": shadow_decision.intent,
                    "reason": shadow_decision.reason,
                    "confidence": shadow_decision.confidence,
                    "agreement": agreement,
                    "model": "qwen2.5:1.5b",
                    "guard_allowed": guard_result.allowed,
                    "guard_reason": guard_result.reason,
                    "authority_allowed": authority_result.allowed,
                    "authority_reason": authority_result.reason,
                },
            }
        )
        await self.broadcast(
            {
                "type": "authority",
                "data": {
                    "allowed": authority_result.allowed,
                    "reason": authority_result.reason,
                    "source": (
                        "ai" if authority_result.allowed else "deterministic"
                    ),
                    "intent": (
                        shadow_decision.intent
                        if authority_result.allowed
                        else work.authoritative_intent
                    ),
                },
            }
        )
        await self.broadcast(
            {"type": "shadow_metrics", "data": self.shadow_metrics.to_dict()}
        )
