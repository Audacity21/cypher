import asyncio

from backend.intelligence.intelligence_engine import IntelligenceDecision
from backend.intelligence.intelligence_guard import IntelligenceGuard
from backend.intelligence.shadow_metrics import ShadowMetrics
from backend.perception.world_state_manager import WorldStateManager
from backend.runtime import CypherRuntime, ShadowWork


class FakeSensorStream:
    async def sensor_stream(self):
        if False:
            yield None


class FakeEventEngine:
    def evaluate(self, previous, current):
        return []


class FakeIntelligence:
    def decide(self, *, event, world_state):
        return IntelligenceDecision(
            intent="PRESENCE",
            reason="Object entered range.",
            confidence=1.0,
        )

    def validate(self, decision):
        return True


class FakeShadowIntelligence:
    def decide(self, event, world_state):
        raise AssertionError("Shadow work must not run in the event path")


class FakeBehavior:
    def __init__(self):
        self.intents = []

    def handle_decision(self, decision):
        self.intents.append(decision.intent)
        return {"status": decision.intent}


def make_runtime(*, subscriber_queue_size=100):
    behavior = FakeBehavior()
    runtime = CypherRuntime(
        sensor_stream=FakeSensorStream(),
        world_state=WorldStateManager(),
        event_engine=FakeEventEngine(),
        intelligence_engine=FakeIntelligence(),
        intelligence_guard=IntelligenceGuard(),
        shadow_intelligence=FakeShadowIntelligence(),
        shadow_metrics=ShadowMetrics(),
        behavior_engine=behavior,
        subscriber_queue_size=subscriber_queue_size,
    )
    return runtime, behavior


def test_event_executes_deterministic_action_before_shadow_work():
    async def scenario():
        runtime, behavior = make_runtime()
        queue = runtime.subscribe()

        await runtime._handle_event(
            {"type": "event", "event": "OBJECT_ENTERED_RANGE", "data": {}},
            {},
        )

        assert behavior.intents == ["PRESENCE"]
        assert runtime._shadow_queue.qsize() == 1

        messages = [queue.get_nowait() for _ in range(queue.qsize())]
        assert [message["type"] for message in messages] == [
            "event",
            "intelligence",
            "action",
        ]

    asyncio.run(scenario())


def test_broadcast_drops_oldest_message_for_slow_subscriber():
    async def scenario():
        runtime, _ = make_runtime(subscriber_queue_size=2)
        queue = runtime.subscribe()

        await runtime.broadcast({"sequence": 1})
        await runtime.broadcast({"sequence": 2})
        await runtime.broadcast({"sequence": 3})

        assert [queue.get_nowait()["sequence"] for _ in range(2)] == [2, 3]

    asyncio.run(scenario())


def test_shadow_queue_keeps_newest_pending_event():
    runtime, _ = make_runtime()
    first = ShadowWork({}, {"sequence": 1}, "IDLE")
    second = ShadowWork({}, {"sequence": 2}, "PRESENCE")

    runtime._enqueue_shadow(first)
    runtime._enqueue_shadow(second)

    assert runtime._shadow_queue.get_nowait() == second
